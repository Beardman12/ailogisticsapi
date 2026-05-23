from abc import ABC, abstractmethod
from typing import Any


class ChatProvider(ABC):
    @abstractmethod
    def generate_reply(self, *, conversation_id: int, prompt: str) -> tuple[str, list[Any]]:
        """Generate assistant reply text and return raw provider events."""
