from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database import get_db
from app.auth import (
    verify_password,
    create_token,
    get_user_from_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
)
from app.schemas import (
    TokenRefresh,
    UserCreate,
    UserCreateResposne,
    TokenResponse,
    SessionCreate,
    SessionCreateResponse,
    SessionResponse,
    ChatCreate,
    ChatResponse,
)
from app.models import UserModel
from app.chat import ChatManager
from app.orm import ORM


router = APIRouter()


@router.get("/")
def read_root():
    return FileResponse("static/login.html")


@router.post("/signup", response_model=UserCreateResposne)
async def signup(user: UserCreate, db: Session = Depends(get_db)):
    """
    새로운 사용자를 등록하는 엔드포인트

    Args: 사용자 생성 정보
    - username: 사용자명
    - password: 비밀번호

    Returns: 생성된 사용자 정보
    - id: 사용자 ID
    - username: 사용자명

    Raises:
    - 400: username 또는 password가 최소 길이 조건을 만족하지 않는 경우
    - 409: 사용자명이 이미 존재하는 경우
    """
    if len(user.username) < 4:
        raise HTTPException(
            status_code=400, detail="Username must be at least 4 characters long."
        )

    if len(user.password) < 6:
        raise HTTPException(
            status_code=400, detail="Password must be at least 6 characters long."
        )

    orm = ORM(db)
    if orm.check_username_exists(user.username):
        raise HTTPException(status_code=409, detail="Username is already taken.")

    new_user = orm.create_user(user)
    return new_user


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """
    사용자 로그인을 처리하는 엔드포인트

    Args: 로그인 폼 데이터
    - username: 사용자명
    - password: 비밀번호

    Returns: 토큰 정보
    - access_token: JWT 액세스 토큰
    - refresh_token: JWT 리프레시 토큰
    - token_type: 토큰 타입 (bearer)

    Raises:
    - 401: 잘못된 사용자명이나 비밀번호
    """
    orm = ORM(db)
    user = orm.get_user_by_username(form_data.username)
    if (
        not user
        or not form_data.password
        or not verify_password(form_data.password, str(user.hashed_password))
    ):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    access_token = create_token(
        str(user.username), timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_token(
        str(user.username), timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_refresh_data: TokenRefresh, db: Session = Depends(get_db)
):
    """
    사용자의 리프레시 토큰을 사용하여 새로운 토큰 세트를 발급하는 엔드포인트

    Args: 기존 리프레시 토큰
    - refresh_token (str): 기존 JWT 리프레시 토큰

    Returns: 토큰 정보
    - access_token: JWT 액세스 토큰
    - refresh_token: JWT 리프레시 토큰
    - token_type: 토큰 타입 (bearer)

    Raises:
    - 401: 리프레시 토큰으로부터 사용자 정보 조회 실패
    """
    user = get_user_from_token(token_refresh_data.refresh_token, db)
    access_token = create_token(
        str(user.username), timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_token(
        str(user.username), timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/session", response_model=SessionCreateResponse)
async def create_session(
    session_create_data: SessionCreate,
    user: UserModel = Depends(get_user_from_token),
    db: Session = Depends(get_db),
):
    """
    ChatGPT와의 새로운 채팅 세션을 생성하는 엔드포인트

    Args: 세션 생성 정보
    - year: 가상인물의 시대 연도
    - location: 가상인물의 위치 정보
    - persona: 가상인물의 페르소나 정보

    Returns: 생성된 세션 정보
    - id: 세션 ID
    """
    orm = ORM(db)
    new_session = orm.create_session(session_create_data, user.id)
    return new_session


@router.get("/session", response_model=list[SessionResponse])
async def get_sessions(
    user: UserModel = Depends(get_user_from_token), db: Session = Depends(get_db)
):
    """
    현재 사용자의 모든 채팅 세션을 가져오는 엔드포인트

    Returns: 세션 목록
    - id: 세션 ID
    - year: 가상인물의 연도 정보
    - location: 가상인물의 위치 정보
    - persona: 가상인물의 인물 정보
    """
    orm = ORM(db)
    sessions = orm.get_sessions_by_user(user.id)
    return sessions


@router.get("/introduction/{session_id}", response_model=ChatResponse)
async def get_introduction(
    session_id: int,
    user: UserModel = Depends(get_user_from_token),
    db: Session = Depends(get_db),
):
    """
    특정 세션에 해당되는 가상인물의 자기소개 문구를 가져오는 엔드포인트

    Args: 세션 ID
    - session_id: 세션 ID (path parameter)

    Returns: 자기소개 응답
    - question: 빈 문자열
    - answer: 가상인물의 자기소개 문구
    """
    chat_manager = ChatManager(session_id, db)
    _, introduction = chat_manager.get_introduction()
    return {"question": "", "answer": introduction}


@router.post("/chat/{session_id}", response_model=list[ChatResponse])
async def chat(
    session_id: int,
    chat_create_data: ChatCreate,
    user: UserModel = Depends(get_user_from_token),
    db: Session = Depends(get_db),
):
    """
    ChatGPT에 새로운 질문 메시지를 전송하고 모든 질문과 답변의 기록을 반환하는 엔드포인트

    Args: 세션 ID와 새로운 질문
    - session_id: 세션 ID (path parameter)
    - question: 사용자의 질문 메시지

    Returns: 채팅 기록 목록 (질문과 답변 쌍의 리스트)
    - question: 사용자 질문 메시지
    - answer: 가상인물의 답변 메시지
    """
    chat_manager = ChatManager(session_id, db)
    question, answer = chat_manager.get_answer(chat_create_data.question)
    orm = ORM(db)
    orm.create_chat(session_id, question, answer)
    chats = orm.get_chats_by_session(session_id)
    chat_list = [{"question": chat.question, "answer": chat.answer} for chat in chats]
    return chat_list


@router.get("/chat/{session_id}", response_model=list[ChatResponse])
async def get_chats(
    session_id: int,
    user: UserModel = Depends(get_user_from_token),
    db: Session = Depends(get_db),
):
    """
    특정 세션의 모든 대화 내역을 가져오는 엔드포인트
    Args: 세션 ID
    - session_id: 세션 ID (path parameter)

    Returns: 채팅 기록 목록 (질문과 답변 쌍의 리스트)
    - question: 사용자 질문 메시지
    - answer: 가상인물의 답변 메시지
    """
    orm = ORM(db)
    chats = orm.get_chats_by_session(session_id)
    chat_list = [{"question": chat.question, "answer": chat.answer} for chat in chats]
    return chat_list
