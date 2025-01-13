from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User, Session, Chat
from app.schemas import UserCreate, SessionCreate
from app.auth import get_hashed_password


class UserORM:
    async def get_user_by_username(self, username: str) -> User | None:
        """사용자 이름으로 유저 조회"""
        query = select(User).filter(User.username == username)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def check_username_exists(self, username: str) -> bool:
        """사용자 이름 존재 여부 확인"""
        return await self.get_user_by_username(username) is not None

    async def create_user(self, user: UserCreate) -> User:
        """새로운 유저 생성"""
        hashed_password = get_hashed_password(user.password)
        new_user = User(username=user.username, hashed_password=hashed_password)
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        return new_user


class SessionORM:
    async def create_session(
        self, session_data: SessionCreate, user_id: int
    ) -> Session:
        """새로운 세션 생성"""
        new_session = Session(user_id=user_id, **session_data.model_dump())
        self.db.add(new_session)
        await self.db.commit()
        await self.db.refresh(new_session)
        return new_session

    async def get_session_by_id(self, session_id: int) -> Session | None:
        """세션 ID로 세션 조회"""
        query = select(Session).filter(Session.id == session_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_sessions_by_user(
        self, user_id: int, get_recent: bool = True, recent_count: int = 5
    ) -> list[Session]:
        """사용자 ID로 세션 조회"""
        query = select(Session).filter(Session.user_id == user_id)
        if get_recent:
            result = await self.db.execute(query)
            return result.mappings().all()
        result = await self.db.execute(query.limit(recent_count))
        return result.mappings().all()


class ChatORM:
    async def create_chat(self, session_id: int, question: str, answer: str) -> Chat:
        """새로운 채팅 생성"""
        new_chat = Chat(session_id=session_id, question=question, answer=answer)
        self.db.add(new_chat)
        await self.db.commit()
        await self.db.refresh(new_chat)
        return new_chat

    async def get_chats_by_session(self, session_id: int) -> list[Chat]:
        """세션 ID로 채팅 내역 조회"""
        query = select(Chat).filter(Chat.session_id == session_id)
        result = await self.db.execute(query)
        return result.mappings().all()


class ORM(UserORM, SessionORM, ChatORM):
    def __init__(self, db: AsyncSession):
        self.db = db
