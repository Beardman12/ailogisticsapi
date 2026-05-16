from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.database import User
from app.models.schemas import ApiResponse, ChatCreateConversationData, ChatMessageData, ChatMessageRequest, MessageOut
from app.services import chat_service
from app.utils.helpers import ok
from app.utils.security import get_current_user

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/history", response_model=ApiResponse)
def create_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    conversation = chat_service.create_conversation(db, current_user)
    data = ChatCreateConversationData(conversation_id=conversation.id)
    return ok(data=data)


@router.get("/history/{conversation_id}", response_model=ApiResponse)
def get_history(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    conversation = chat_service.get_conversation(db, current_user, conversation_id)
    messages = chat_service.list_messages(db, conversation)
    return ok(data=[MessageOut.model_validate(item) for item in messages])


@router.post("/message", response_model=ApiResponse)
def send_message(
    payload: ChatMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    if payload.conversation_id is None:
        conversation = chat_service.create_conversation(db, current_user)
    else:
        conversation = chat_service.get_conversation(db, current_user, payload.conversation_id)

    history_messages = chat_service.list_messages(db, conversation)
    prompt = chat_service.build_conversation_prompt(history_messages, payload.message)

    chat_service.add_message(db, conversation, role="user", content=payload.message)
    assistant_reply, stream_events = chat_service.request_coze_reply(
        conversation=conversation,
        prompt=prompt,
    )
    chat_service.add_message(db, conversation, role="assistant", content=assistant_reply)

    data = ChatMessageData(
        conversation_id=conversation.id,
        message=assistant_reply,
        stream_events=stream_events,
    )
    return ok(data=data)
