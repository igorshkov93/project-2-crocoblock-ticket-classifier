"""Core classifier: text in -> TicketClassification out (Google Gemini)."""

import os
import time
from dataclasses import dataclass

from dotenv import load_dotenv
from google import genai
from google.genai import types

from schema import TicketClassification
from prompts import SYSTEM_INSTRUCTION

load_dotenv()

# gemini-2.5-flash: fast, free-tier friendly. Swap via GEMINI_MODEL in your .env
# (e.g. gemini-2.5-flash-lite for higher RPM, gemini-3.5-flash for newer).
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

_client = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError(
                "No API key found. Put GEMINI_API_KEY=... in your .env "
                "(get a free key at https://aistudio.google.com/apikey)."
            )
        _client = genai.Client(api_key=api_key)
    return _client


@dataclass
class ClassificationResult:
    """The parsed label plus a bit of run metadata (handy for automation dashboards)."""
    label: TicketClassification
    model: str
    latency_ms: int
    input_tokens: int
    output_tokens: int


def classify_ticket(text: str, model: str | None = None) -> ClassificationResult:
    """Classify a single support ticket.

    Few-shot examples live in the system instruction; the schema is enforced by Gemini,
    so `response.parsed` is already a validated `TicketClassification` — not a raw string.
    """
    client = _get_client()
    model = model or MODEL

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        response_mime_type="application/json",
        response_schema=TicketClassification,
        temperature=0,  # deterministic triage
    )

    start = time.perf_counter()
    response = client.models.generate_content(model=model, contents=text, config=config)
    latency_ms = int((time.perf_counter() - start) * 1000)

    label = response.parsed
    if label is None:
        raise RuntimeError(f"Model did not return structured output. Raw: {response.text}")

    usage = response.usage_metadata
    return ClassificationResult(
        label=label,
        model=model,
        latency_ms=latency_ms,
        input_tokens=getattr(usage, "prompt_token_count", 0) or 0,
        output_tokens=getattr(usage, "candidates_token_count", 0) or 0,
    )
