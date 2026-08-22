"""
LLM service — thin wrapper around the Groq API.

Responsibilities:
- Build chat completion requests for Groq.
- Return the raw text response.
- Handle Groq errors safely (never expose API keys or stack traces).

Does NOT implement RAG logic — that lives in rag_service.py.
"""
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

# Groq client is lazy-initialized on first use
_groq_client = None


def _get_groq_client():
    global _groq_client
    if _groq_client is None:
        from groq import Groq
        from app.config import get_settings
        settings = get_settings()
        _groq_client = Groq(api_key=settings.GROQ_API_KEY)
    return _groq_client


class LLMError(Exception):
    """Raised when the LLM call fails in an unrecoverable way."""


def chat_complete(
    messages: List[Dict[str, str]],
    model: str = None,
    temperature: float = 0.1,
    max_tokens: int = 1024,
) -> str:
    """
    Send a list of chat messages to Groq and return the assistant's reply.

    messages: [{"role": "system"|"user"|"assistant", "content": "..."}]
    Returns the content string of the first completion choice.
    Raises LLMError on failure.
    """
    from app.config import get_settings
    settings = get_settings()
    model = model or settings.GROQ_MODEL

    try:
        client = _get_groq_client()
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content or ""
        return content.strip()
    except Exception as exc:
        # Log full details internally but never expose them
        logger.exception("Groq API call failed")
        raise LLMError("LLM call failed") from exc
