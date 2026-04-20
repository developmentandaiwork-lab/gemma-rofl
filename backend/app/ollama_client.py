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


def generate_embedding(text: str) -> list[float]:
    endpoint = f"{settings.ollama_base_url.rstrip('/')}/api/embeddings"
    payload = {"model": settings.ollama_embedding_model, "prompt": text}

    try:
        with httpx.Client(timeout=settings.ollama_timeout) as client:
            response = client.post(endpoint, json=payload)
            response.raise_for_status()
            data = response.json()
    except Exception as exc:
        logger.exception("Ollama embedding failed: %s", exc)
        raise RuntimeError("Embedding generation failed") from exc

    embedding = data.get("embedding")
    if not isinstance(embedding, list) or not embedding:
        raise RuntimeError("Invalid embedding response")
    return [float(v) for v in embedding]
