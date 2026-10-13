"""
Kompatibilitätshilfen für OpenAI Chat Completions
(portiert aus Upstream 666ghj/MiroFish: f7138e0, e67a52e)

Behält das bisherige Anfrageformat für alle Modelle/Anbieter bei und passt die
Parameter nur für Modelle der GPT-5-Familie an. Lokale Anbieter (Ollama, LM Studio)
sind davon nicht betroffen; ihre Zusatzparameter (z.B. extra_body mit
reasoning_effort) werden unverändert durchgereicht.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def is_gpt5_family(model: Optional[str]) -> bool:
    """True, wenn das Modell zur GPT-5-Familie (Aliase/Snapshots) gehört."""
    if not model:
        return False
    return model.strip().lower().startswith("gpt-5")


def create_chat_completion(
    client: Any,
    *,
    model: str,
    messages: List[Dict[str, Any]],
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    response_format: Optional[Dict[str, Any]] = None,
    **extra_kwargs: Any,
) -> Any:
    """
    Chat-Completion mit modellspezifischen Anfrageparametern erstellen.

    Strategie:
    - GPT-5-Familie: standardmäßig keine temperature senden.
    - Token-Grenze: `max_completion_tokens` bei GPT-5, sonst `max_tokens`.
    - Für alle anderen Modelle/Anbieter bleibt das bisherige Anfrageformat erhalten.
    - Fehler des Anbieters werden unverändert weitergereicht, statt aus Meldungstexten zu raten.
    - Weitere Parameter (z.B. extra_body für lokale Anbieter) werden unverändert übergeben.
    """
    kwargs: Dict[str, Any] = {
        "model": model,
        "messages": messages,
    }

    if response_format is not None:
        kwargs["response_format"] = response_format

    gpt5_family = is_gpt5_family(model)

    if temperature is not None and not gpt5_family:
        kwargs["temperature"] = temperature

    if max_tokens is not None:
        if gpt5_family:
            kwargs["max_completion_tokens"] = max_tokens
        else:
            kwargs["max_tokens"] = max_tokens

    kwargs.update(extra_kwargs)

    return client.chat.completions.create(**kwargs)


def extract_chat_completion_text(response: Any) -> str:
    """Reinen Text aus einer Chat-Completion lesen, unabhängig von der Inhaltsform des SDK."""
    choices = getattr(response, "choices", None) or []
    if not choices:
        return ""

    message = getattr(choices[0], "message", None)
    if message is None:
        return ""

    content = getattr(message, "content", "")

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        chunks: List[str] = []
        for item in content:
            if isinstance(item, dict):
                text_obj = item.get("text")
                if isinstance(text_obj, dict):
                    text_obj = text_obj.get("value")
                if isinstance(text_obj, str):
                    chunks.append(text_obj)
                elif isinstance(item.get("content"), str):
                    chunks.append(item["content"])
                continue

            text_obj = getattr(item, "text", None)
            if isinstance(text_obj, dict):
                text_obj = text_obj.get("value")
            if isinstance(text_obj, str):
                chunks.append(text_obj)
                continue

            content_obj = getattr(item, "content", None)
            if isinstance(content_obj, str):
                chunks.append(content_obj)

        return "".join(chunks).strip()

    return str(content or "")
