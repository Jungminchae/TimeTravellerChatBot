import os
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv
from passlib.context import CryptContext
from datetime import datetime, timezone, timedelta
from jose import jwt, JWTError
from app.database import get_db
from app.orm import ORM

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "test_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def get_hashed_password(password: str):
    """
    주어진 평문 비밀번호를 해시화

    Args:
        password (str): 해시화할 평문 비밀번호

    Returns:
        str: PBKDF2-SHA256으로 해시화된 비밀번호
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str):
    """
    평문 비밀번호와 해시화된 비밀번호가 일치하는지 검증

    Args:
        plain_password (str): 검증할 평문 비밀번호
        hashed_password (str): 저장된 해시화된 비밀번호

    Returns:
        bool: 비밀번호 일치 여부
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_token(username: str, expires_delta: timedelta):
    """
    사용자 인증을 위한 JWT 토큰을 생성

    Args:
        username (str): 토큰에 포함될 사용자 이름

    Returns:
        str: 생성된 JWT 토큰

    Notes:
        - 액세스 토큰은 현재 시간으로부터 ACCESS_TOKEN_EXPIRE_MINUTES 분 후에 만료.
        - 리프레시 토큰은 현재 시간으로부터 REFRESH_TOKEN_EXPIRE_DAYS 일 후에 만료.
        - 토큰에는 사용자 이름(sub)과 만료 시간(exp)이 포함됨.
    """
    encode_data = {
        "sub": username,
        "exp": datetime.now(timezone.utc) + expires_delta,
    }
    return jwt.encode(encode_data, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str):
    """
    JWT 토큰의 유효성을 검증

    Args:
        token (str): 검증할 JWT 토큰

    Returns:
        dict | None: 토큰이 유효한 경우 디코딩된 페이로드, 유효하지 않은 경우 None
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_user_from_token(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
):
    """
    JWT 토큰으로부터 현재 인증된 사용자를 조회

    Args:
        token (str): Bearer 토큰 (FastAPI의 oauth2_scheme을 통해 자동으로 주입됨)
        db (Session): 데이터베이스 세션 (FastAPI의 의존성 주입을 통해 자동으로 주입됨)

    Returns:
        UserModel: 인증된 사용자 모델 인스턴스

    Raises:
        HTTPException: 다음의 경우 401 Unauthorized 예외가 발생:
            - 토큰이 유효하지 않은 경우
            - 토큰에서 사용자 이름을 추출할 수 없는 경우
            - 데이터베이스에서 해당 사용자를 찾을 수 없는 경우
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verify_token(token)
    if payload is None:
        raise credentials_exception
    username = payload.get("sub")
    if username is None:
        raise credentials_exception
    orm = ORM(db)
    user = await orm.get_user_by_username(username)
    if user is None:
        raise credentials_exception
    return user
