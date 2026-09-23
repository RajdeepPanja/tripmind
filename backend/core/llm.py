"""
Groq LLM client wrapper — centralizes model selection and error handling
so agents never touch langchain_groq directly, and can accept an injected
fake in tests instead of constructing a real client.
"""
from __future__ import annotations

from langchain_groq import ChatGroq

from core.config import settings


class LLMError(Exception):
    """Raised when the LLM client cannot be constructed or called."""


def get_groq_llm(temperature: float = 0.3) -> ChatGroq:
    if not settings.groq_api_key:
        raise LLMError(
            "GROQ_API_KEY is not set. Add it to backend/.env before generating "
            "an itinerary."
        )
    return ChatGroq(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
        temperature=temperature,
        timeout=30.0,
        max_retries=1,
    )