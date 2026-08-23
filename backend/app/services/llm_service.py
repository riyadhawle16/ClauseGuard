"""
LLM service — thin wrapper around the Groq API.

Responsibilities:
- Build chat completion requests for Groq.
- Return the raw text response.
- Handle Groq errors safely (never expose API keys or stack traces).
- Log the specific failure reason for operator diagnosis.
"""
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

# Groq client is lazy-initialized on first use.
# NOT cached as a module singleton — re-created each call so that
# an updated API key in config is always picked up.
_groq_client = None


def _get_groq_client():
    """
    Return a Groq client.  Re-initialises if GROQ_API_KEY has changed
    (avoids stale-client issues when the key was empty on startup).
    """
    global _groq_client
    from app.config import get_settings
    settings = get_settings()

    if not settings.GROQ_API_KEY:
        raise LLMError("GROQ_API_KEY is not configured. Set it in backend/.env.")

    # Always use the current key — cheap to construct
    from groq import Groq
    return Groq(api_key=settings.GROQ_API_KEY)


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
    Raises LLMError on failure with a logged reason (no API key exposed).
    """
    from app.config import get_settings
    settings = get_settings()
    model = model or settings.GROQ_MODEL

    try:
        client = _get_groq_client()
        logger.debug("Calling Groq model=%s, messages=%d", model, len(messages))
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content or ""
        logger.debug("Groq responded with %d characters", len(content))
        return content.strip()

    except LLMError:
        # Re-raise our own errors (e.g. missing key) unchanged
        raise

    except Exception as exc:
        # Classify the error for operator logs without exposing API key
        exc_str = str(exc).lower()
        if "401" in exc_str or "authentication" in exc_str or "api_key" in exc_str or "invalid_api_key" in exc_str:
            reason = "Groq authentication error — check GROQ_API_KEY in backend/.env"
        elif "429" in exc_str or "rate_limit" in exc_str or "rate limit" in exc_str:
            reason = "Groq rate limit exceeded — try again shortly"
        elif "model_not_found" in exc_str or "model" in exc_str and "not found" in exc_str:
            reason = f"Groq model '{model}' not found — update GROQ_MODEL in backend/.env"
        elif "connection" in exc_str or "network" in exc_str or "timeout" in exc_str:
            reason = "Groq network/connection error — check internet connectivity"
        elif "invalid" in exc_str and "request" in exc_str:
            reason = "Groq rejected the request — malformed prompt or request"
        else:
            reason = f"Groq API error: {type(exc).__name__}"

        logger.error("LLM call failed [%s]: %s", reason, type(exc).__name__)
        raise LLMError(reason) from exc
