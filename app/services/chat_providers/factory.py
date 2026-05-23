from functools import lru_cache

from fastapi import HTTPException

from app.config import settings
from app.services.chat_providers.base import ChatProvider
from app.services.chat_providers.coze_provider import CozeChatProvider
from app.services.chat_providers.dify_provider import DifyChatProvider


@lru_cache(maxsize=1)
def get_chat_provider() -> ChatProvider:
    provider_name = settings.ai_provider.lower().strip()

    if provider_name == "coze":
        return CozeChatProvider()
    if provider_name == "dify":
        return DifyChatProvider()

    raise HTTPException(status_code=500, detail=f"Unsupported AI provider: {settings.ai_provider}")
