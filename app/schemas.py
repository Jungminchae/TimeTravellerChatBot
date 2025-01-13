from pydantic import BaseModel, model_validator


class UserCreate(BaseModel):
    """
    사용자 생성 요청을 위한 스키마

    Attributes:
    - username (str): 생성할 사용자의 고유한 사용자명
    - password (str): 사용자의 평문 비밀번호
    """

    username: str
    password: str

    @model_validator(mode="before")
    @classmethod
    def validate(cls, data):
        if len(data.username) < 4:
            raise ValueError("Username must be at least 4 characters long.")

        if len(data.password) < 6:
            raise ValueError("Password must be at least 6 characters long.")
        return data


class UserCreateResposne(BaseModel):
    """
    사용자 생성 응답을 위한 스키마

    Attributes:
    - username (str): 생성된 사용자의 사용자명
    - id (int): 생성된 사용자의 고유 ID
    """

    username: str
    id: int


class TokenResponse(BaseModel):
    """
    인증 토큰 응답을 위한 스키마

    Attributes:
    - access_token (str): JWT 형식의 액세스 토큰
    - refresh_token (str): JWT 형식의 리프레시 토큰
    - token_type (str): 토큰 타입 (예: "bearer")
    """

    access_token: str
    refresh_token: str
    token_type: str


class TokenRefresh(BaseModel):
    """
    인증 토큰 갱신 요청을 위한 스키마

    Attributes:
    - refresh_token (str): JWT 형식의 리프레시 토큰
    """

    refresh_token: str


class SessionCreate(BaseModel):
    """
    대화 세션 생성 요청을 위한 스키마

    Attributes:
    - year (int): 세션의 연도 설정값
    - location (str): 세션의 위치 설정값
    - persona (str): 세션의 인물 설정값
    """

    year: int
    location: str
    persona: str


class SessionCreateResponse(BaseModel):
    """
    대화 세션 생성 응답을 위한 스키마

    Attributes:
    - id (int): 생성된 세션의 고유 ID
    """

    id: int


class SessionResponse(BaseModel):
    """
    채팅 세션 정보를 반환하기 위한 스키마

    Attributes:
    - id (int): 세션의 고유 ID
    - year (int): 세션의 연도 설정값
    - location (str): 세션의 위치 설정값
    - persona (str): 세션의 인물 설정값
    """

    id: int
    year: int
    location: str
    persona: str


class ChatCreate(BaseModel):
    """
    채팅 메시지 생성 요청을 위한 스키마

    Attributes:
    - question (str): 사용자의 질문 내용
    """

    question: str


class ChatResponse(BaseModel):
    """
    채팅 메시지 응답을 위한 스키마

    Attributes:
        question (str): 사용자가 보낸 원본 질문
        answer (str): ChatGPT가 생성한 응답
    """

    question: str
    answer: str
