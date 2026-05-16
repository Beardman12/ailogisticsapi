import json
from collections.abc import Iterable
from time import perf_counter
from typing import Any

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.models.database import Conversation, Message, User
from app.utils.logging import log_external_api_interaction


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
    lines: list[str] = []
    for message in history_messages:
        if message.role == "user":
            lines.append(f"用户:{message.content}")
            continue
        if message.role == "assistant":
            lines.append(f"系统:{message.content}")

    lines.append(f"用户:{current_user_message}")
    return "\n".join(lines)


def _extract_text_fragments(payload: Any) -> list[str]:
    fragments: list[str] = []

    def walk(node: Any) -> None:
        if node is None:
            return
        if isinstance(node, (str, int, float, bool)):
            return
        if isinstance(node, list):
            for item in node:
                walk(item)
            return
        if not isinstance(node, dict):
            return

        for key in ("text", "answer", "output_text"):
            value = node.get(key)
            if isinstance(value, str) and value:
                fragments.append(value)

        content = node.get("content")
        if isinstance(content, str) and content:
            fragments.append(content)
        elif isinstance(content, dict):
            text = content.get("text")
            if isinstance(text, str) and text:
                fragments.append(text)
            for key, value in content.items():
                if key == "text":
                    continue
                walk(value)
        elif isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    text = item.get("text")
                    if isinstance(text, str) and text:
                        fragments.append(text)
                    for key, value in item.items():
                        if key == "text":
                            continue
                        walk(value)
                    continue
                walk(item)

        delta = node.get("delta")
        if delta is not None:
            walk(delta)

        choices = node.get("choices")
        if isinstance(choices, list):
            walk(choices)

        output = node.get("output")
        if output is not None:
            walk(output)

        for key, value in node.items():
            if key in {"text", "answer", "output_text", "content", "delta", "choices", "output"}:
                continue
            walk(value)

    walk(payload)
    return fragments


def _iter_stream_events(lines: Iterable[str]) -> list[Any]:
    events: list[Any] = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("event:"):
            continue

        if line.startswith("data:"):
            line = line[len("data:") :].strip()
        if not line or line == "[DONE]":
            continue

        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            events.append({"raw": line})
    return events


def request_coze_reply(
    *,
    conversation: Conversation,
    prompt: str,
) -> tuple[str, list[Any]]:
    if not settings.coze_stream_run_url:
        raise HTTPException(status_code=500, detail="COZE_STREAM_RUN_URL is not configured")
    if not settings.coze_token:
        raise HTTPException(status_code=500, detail="COZE_TOKEN is not configured")
    if not settings.coze_project_id:
        raise HTTPException(status_code=500, detail="COZE_PROJECT_ID is not configured")

    request_payload = {
        "content": {
            "query": {
                "prompt": [
                    {
                        "type": "text",
                        "content": {
                            "text": prompt,
                        },
                    }
                ]
            }
        },
        "type": "query",
        "session_id": f"conv_{conversation.id}",
        "project_id": settings.coze_project_id,
    }

    headers = {
        "Authorization": f"Bearer {settings.coze_token}",
        "Content-Type": "application/json",
    }
    request_url = settings.coze_stream_run_url
    start = perf_counter()

    try:
        with httpx.Client(timeout=60.0) as client:
            with client.stream(
                "POST",
                request_url,
                headers=headers,
                json=request_payload,
            ) as response:
                response.raise_for_status()
                events = _iter_stream_events(response.iter_lines())
                log_external_api_interaction(
                    service_name="coze",
                    method="POST",
                    url=request_url,
                    request_headers=headers,
                    request_body=request_payload,
                    status_code=response.status_code,
                    response_body=events,
                    elapsed_ms=(perf_counter() - start) * 1000,
                )
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text if exc.response is not None else ""
        log_external_api_interaction(
            service_name="coze",
            method="POST",
            url=request_url,
            request_headers=headers,
            request_body=request_payload,
            status_code=exc.response.status_code if exc.response is not None else None,
            response_body=detail,
            elapsed_ms=(perf_counter() - start) * 1000,
            error="HTTPStatusError",
        )
        raise HTTPException(status_code=502, detail=f"Coze API request failed: {detail}") from exc
    except httpx.HTTPError as exc:
        log_external_api_interaction(
            service_name="coze",
            method="POST",
            url=request_url,
            request_headers=headers,
            request_body=request_payload,
            status_code=None,
            elapsed_ms=(perf_counter() - start) * 1000,
            error=str(exc),
        )
        raise HTTPException(status_code=502, detail="Coze API is unavailable") from exc

    text_fragments: list[str] = []
    for event in events:
        text_fragments.extend(_extract_text_fragments(event))

    full_text = "".join(text_fragments).strip()
    if not full_text:
        raise HTTPException(status_code=502, detail="Failed to parse Coze streamed response")
    return full_text, events
