"""Standalone OpenRouter API client for the FMG-Bench runner."""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class OpenRouterCallError(Exception):
    """OpenRouter call failed with details suitable for benchmark telemetry."""

    def __init__(self, message: str, details: dict[str, Any]) -> None:
        super().__init__(message)
        self.details = details


async def call_openrouter_model(
    model: str,
    messages: list[dict],
    temperature: float = 0.7,
    max_tokens: int = 2000,
    timeout_seconds: float = 120.0,
) -> dict:
    """
    Call the OpenRouter chat completions API.

    Returns a dict with keys: content, raw_response, response_id, requested_model,
    returned_model, finish_reason, native_finish_reason, usage, latency_ms, request.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not found in environment variables")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://fideai.org",
        "X-Title": "FMG-Bench Evaluation",
    }

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    started_at = time.perf_counter()
    async with httpx.AsyncClient(timeout=timeout_seconds) as client:
        try:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            latency_ms = round((time.perf_counter() - started_at) * 1000, 3)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            latency_ms = round((time.perf_counter() - started_at) * 1000, 3)
            raise OpenRouterCallError(
                f"OpenRouter API error: {exc.response.status_code}",
                {
                    "status_code": exc.response.status_code,
                    "response_text": exc.response.text,
                    "latency_ms": latency_ms,
                    "request": {
                        "model": model,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "timeout_seconds": timeout_seconds,
                        "message_count": len(messages),
                    },
                },
            ) from exc
        except httpx.TimeoutException as exc:
            latency_ms = round((time.perf_counter() - started_at) * 1000, 3)
            raise OpenRouterCallError(
                f"OpenRouter API timeout for model {model}",
                {
                    "latency_ms": latency_ms,
                    "request": {
                        "model": model,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "timeout_seconds": timeout_seconds,
                        "message_count": len(messages),
                    },
                },
            ) from exc

    data = response.json()
    choices = data.get("choices")
    if not choices:
        raise ValueError(
            f"OpenRouter response missing choices for model {model}: {json.dumps(data)[:500]}"
        )
    message = choices[0].get("message", {})
    content = message.get("content")
    if not isinstance(content, str):
        raise ValueError(
            f"OpenRouter response missing message content for model {model}: {json.dumps(data)[:500]}"
        )
    choice = choices[0]
    return {
        "content": content,
        "raw_response": data,
        "response_id": data.get("id"),
        "requested_model": model,
        "returned_model": data.get("model"),
        "finish_reason": choice.get("finish_reason"),
        "native_finish_reason": choice.get("native_finish_reason"),
        "usage": data.get("usage", {}),
        "latency_ms": latency_ms,
        "request": {
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "timeout_seconds": timeout_seconds,
            "message_count": len(messages),
        },
    }
