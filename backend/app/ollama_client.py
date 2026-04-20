import logging

import httpx
from fastapi import HTTPException, status

from app.config import settings

logger = logging.getLogger(__name__)


def generate_assistant_reply(messages: list[dict[str, str]]) -> str:
    payload = {"model": settings.ollama_model, "messages": messages}
    endpoint = f"{settings.ollama_base_url.rstrip('/')}/v1/chat/completions"

    try:
        with httpx.Client(timeout=settings.ollama_timeout) as client:
            response = client.post(endpoint, json=payload)
            response.raise_for_status()
            data = response.json()
    except httpx.RequestError as exc:
        logger.exception("Ollama request failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Ollama is unavailable")
    except httpx.HTTPStatusError as exc:
        logger.exception("Ollama returned error status: %s", exc)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Ollama returned an error")
    except Exception as exc:
        logger.exception("Unexpected Ollama error: %s", exc)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Invalid Ollama response")

    try:
        return data["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        logger.exception("Malformed Ollama payload: %s", exc)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Malformed Ollama response")
