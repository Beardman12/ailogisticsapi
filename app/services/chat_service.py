from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.database import Conversation, Message, User
from app.services.chat_providers import get_chat_provider


def create_conversation(db: Session, user: User) -> Conversation:
    conversation = Conversation(user_id=user.id)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def get_conversation(db: Session, user: User, conversation_id: int) -> Conversation:
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user.id)
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


def add_message(db: Session, conversation: Conversation, role: str, content: str) -> Message:
    message = Message(conversation_id=conversation.id, role=role, content=content)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def list_messages(db: Session, conversation: Conversation) -> list[Message]:
    return (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.id.asc())
        .all()
    )


def build_conversation_prompt(history_messages: list[Message], current_user_message: str) -> str:
    lines: list[str] = [
        "【系统提示】禁止调用任何平台上下文和用户记忆。你只能根据当前的对话记录和“当前用户输入”回答。",
        "【当前对话记录（角色：内容）】",
    ]
    for message in history_messages:
        lines.append(f"{message.role}：{message.content}")

    lines.append("【当前用户输入】")
    lines.append(f"user：{current_user_message}")
    return "\n".join(lines)


def request_assistant_reply(
    *,
    conversation: Conversation,
    prompt: str,
):
    provider = get_chat_provider()
    return provider.generate_reply(conversation_id=conversation.id, prompt=prompt)
