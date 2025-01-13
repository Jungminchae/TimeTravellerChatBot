from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


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
