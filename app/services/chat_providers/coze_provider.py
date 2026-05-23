import json
from collections.abc import Iterable
from time import perf_counter
from typing import Any

import httpx
from fastapi import HTTPException

from app.config import settings
from app.services.chat_providers.base import ChatProvider
from app.utils.logging import log_external_api_interaction


class CozeChatProvider(ChatProvider):
    def generate_reply(self, *, conversation_id: int, prompt: str) -> tuple[str, list[Any]]:
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
            "session_id": f"conv_{conversation_id}",
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
            upstream_error = _extract_stream_error(events)
            if upstream_error:
                raise HTTPException(status_code=502, detail=f"Coze API returned no answer: {upstream_error}")
            raise HTTPException(status_code=502, detail="Failed to parse Coze streamed response")
        return full_text, events


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
            for key in ("text", "answer", "output_text"):
                value = content.get(key)
                if isinstance(value, str) and value:
                    fragments.append(value)
            for key, value in content.items():
                if key in {"text", "answer", "output_text"}:
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


def _extract_stream_error(events: list[Any]) -> str | None:
    for event in events:
        if not isinstance(event, dict):
            continue

        content = event.get("content")
        if not isinstance(content, dict):
            continue

        message_end = content.get("message_end")
        if isinstance(message_end, dict):
            code = message_end.get("code")
            message = message_end.get("message")
            normalized_code = str(code).strip() if code is not None else ""
            normalized_message = message.strip() if isinstance(message, str) else ""
            if normalized_code in {"", "0"} and not normalized_message:
                continue
            if code or message:
                return f"code={code}, message={message}" if code else str(message)

        event_error = content.get("error")
        if isinstance(event_error, dict):
            code = event_error.get("code")
            message = event_error.get("message")
            if code or message:
                return f"code={code}, message={message}" if code else str(message)
        if isinstance(event_error, str) and event_error.strip():
            return event_error

    return None
