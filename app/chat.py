import asyncio
import requests
from dataclasses import dataclass
from app.orm import ORM

URL_ENDPOINT = "https://open-api.jejucodingcamp.workers.dev/"


@dataclass
class Message:
    """ChatGPT와 대화했던 개별 질문과 대답을 저장하기 위한 클래스"""

    role: str
    content: str

    def to_dict(self):
        return {"role": self.role, "content": self.content}


class ChatHistory:
    """ChatGPT과 대화의 개별 내역인 Message들을 목록으로 저장하기 위한 클래스"""

    def __init__(self):
        self._messages: list[Message] = []

    def __getitem__(self, index):
        return self._messages[index]

    def __len__(self):
        return len(self._messages)

    def append(self, message):
        self._messages.append(message)

    def clear(self):
        self._messages.clear()

    def convert_messages_to_dict_list(self):
        """Message 목록의 개별 Message 객체를 ChatGPT가 이해하는 dict 형태로 변환하기"""
        return [msg.to_dict() for msg in self._messages]


class ChatManager:
    """
    ChatGPT 통신하기 위한 매니저 클래스

    [작동 방식]
    1. 초기화 시점에 Session 정보를 받아서 Session에 속한 모든 Chat 정보를 Message로 변환하여 신규 ChatHistory 객체로 통합.
    2. ChatGPT에 자기소개(introduction)를 요청할 때, ChatHistory에 prompt 질문 추가하여 전송.
    3. ChatGPT에 새로운 질문을 요청할 때, ChatHistory에 해당 질문 추가하여 전송.
    """

    def __init__(self, session_id, db):
        self.session_id = session_id
        self.orm = ORM(db)
        self.url_endpoint = URL_ENDPOINT
        self.chat_history = asyncio.run(self.gather_chat_history())

    async def gather_chat_history(self):
        """Session에 속한 모든 Chat의 질문과 대답을 Message로 변환하여 ChatHistory 객체로 통합하기"""

        session = await self.orm.get_session_by_id(self.session_id)
        chat_history = ChatHistory()
        if session:
            chat_list = session.chats
            if len(chat_list) > 0:
                chat_history.append(
                    Message(role="system", content=str(chat_list[0].question))
                )
                chat_history.append(
                    Message(role="assistant", content=str(chat_list[0].answer))
                )
                for chat in chat_list[1:]:
                    print(f"[Q] {chat.question} [A] {chat.answer}")
                    chat_history.append(
                        Message(role="user", content=str(chat.question))
                    )
                    chat_history.append(
                        Message(role="assistant", content=str(chat.answer))
                    )
        return chat_history

    def send_question_with_history(self):
        """ChatGPT에 ChatHistory를 포맷 변환하여 질문을 보내고 답변 받기"""

        messages_dict_list = self.chat_history.convert_messages_to_dict_list()
        response = requests.post(url=self.url_endpoint, json=messages_dict_list)
        # TODO: request 에러처리
        return response.json()["choices"][0]["message"]["content"]

    def add_question_into_history_and_get_answer(self, role, question):
        """새로운 질문을 기존 ChatHistory에 추가한 후, 전체 ChatHistory를 ChatGPT에게 전송해서 답변 받기"""

        self.chat_history.append(Message(role=role, content=question))
        answer = self.send_question_with_history()
        return answer

    async def get_introduction(self):
        """ChatGPT가 수행할 역할을 설정하고, 자기소개 멘트를 확보하기"""

        def _make_introduction_prompt_message(year, location, persona):
            """ChatGPT가 수행할 역할을 설정하는 prompt 메시지 생성하기"""
            prompt = (
                f"너는 {year}년에 {location} 지역에 살고 있는 '{persona}'인 사람이야. "
                f"이 조건에 부합하는 실제 역사의 인물을 반드시 찾아보고, 찾았다면 그 사람인 것처럼 말해줘. "
                f"못 찾았다면 최대한 그 시대와 지역에 있었을 법한 사람인 것처럼 대답해줘."
                f"앞으로 말투도 그런 사람인 것처럼 대답해. 그렇지만 한국어로 말해야 해. "
                f"너의 시대와 지역을 벗어나는 지식, 기술, 용어 등에 대해서는 전혀 몰라야 해. "
                f"이름을 반드시 포함해서, 짧게 너 자신을 소개해줘."
            )
            return prompt

        session = await self.orm.get_session_by_id(self.session_id)
        chat_list = session.chats
        if len(chat_list) > 0:
            chat = chat_list[0]
            return chat.question, chat.answer

        introduction_prompt = _make_introduction_prompt_message(
            year=session.year, location=session.location, persona=session.persona
        )
        introduction = self.add_question_into_history_and_get_answer(
            role="system", question=introduction_prompt
        )
        await self.orm.create_chat(self.session_id, introduction_prompt, introduction)
        return introduction_prompt, introduction

    def get_answer(self, question):
        """ChatGPT에게 새로운 질문을 하고 답변 받기"""

        answer = self.add_question_into_history_and_get_answer(
            role="user", question=question
        )
        return question, answer
