from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship, mapped_column, Mapped
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    """
    사용자 정보를 저장하는 모델

    Attributes:
        id (int): 사용자의 고유 식별자
        username (str): 사용자의 고유한 사용자명
        hashed_password (str): PBKDF2-SHA256으로 해시화된 비밀번호
        sessions (list[SessionModel]): 사용자의 대화 세션 목록

    Relationships:
        - sessions: 일대다 관계로 SessionModel과 연결됨
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    sessions: Mapped[list["Session"]] = relationship(
        "Session", back_populates="user", cascade="all, delete-orphan"
    )


class Session(Base):
    """
    대화 세션 정보를 저장하는 모델

    Attributes:
        id (int): 세션의 고유 식별자
        user_id (int): 세션을 소유한 사용자의 ID (Foreign Key)
        year (int): 세션의 연도 설정
        location (str): 세션의 위치 설정
        persona (str): 세션의 인물 설정
        created_at (datetime): 세션 생성 시간

    Relationships:
        - user: 다대일 관계로 User과 연결됨
        - chats: 일대다 관계로 Chat과 연결됨
    """

    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE")
    )
    year: Mapped[int] = mapped_column(Integer)
    location: Mapped[str] = mapped_column(String)
    persona: Mapped[str] = mapped_column(String)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped[User] = relationship("UserModel", back_populates="sessions")
    chats: Mapped[list["Chat"]] = relationship(
        "Chat", back_populates="session", cascade="all, delete-orphan"
    )


class Chat(Base):
    """
    개별 대화 내용을 저장하는 모델

    Attributes:
        id (int): 대화의 고유 식별자
        session_id (int): 대화가 속한 세션의 ID (Foreign Key)
        question (str): 사용자의 질문 내용
        answer (str): ChatGPT의 응답 내용
        created_at (datetime): 대화 생성 시간

    Relationships:
        - session: 다대일 관계로 Session과 연결됨
    """

    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sessions.id", ondelete="CASCADE")
    )
    question: Mapped[str] = mapped_column(String)
    answer: Mapped[str] = mapped_column(String)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    session: Mapped["Session"] = relationship("Session", back_populates="chats")
