from typing import Any

from fastapi import HTTPException

from app.services.chat_providers.base import ChatProvider


class DifyChatProvider(ChatProvider):
    def generate_reply(self, *, conversation_id: int, prompt: str) -> tuple[str, list[Any]]:
        _ = conversation_id
        _ = prompt
        raise HTTPException(status_code=501, detail="Dify provider is not implemented yet")
