"""
LLM-Client-Wrapper
Einheitliche Verwendung des OpenAI-Formats
Unterstützt: OpenAI, LM Studio, Ollama und andere OpenAI-kompatible APIs
"""

import json
import logging
import os
import re
from typing import Optional, Dict, Any, List
from openai import OpenAI

from ..config import Config
from .openai_chat_compat import create_chat_completion, extract_chat_completion_text


logger = logging.getLogger(__name__)


class LLMResponseError(ValueError):
    """Sicherer, strukturierter Fehler für unbrauchbare Modellantworten (Upstream f0d487f)."""

    def __init__(self, message: str, *, finish_reason: Optional[str] = None):
        super().__init__(message)
        self.finish_reason = finish_reason


def _is_response_format_unsupported(error: Exception) -> bool:
    """Erkennt, ob der Anbieter response_format (JSON-Modus) ausdrücklich ablehnt."""

    if getattr(error, "status_code", None) not in {400, 422}:
        return False

    body = getattr(error, "body", None)
    if not isinstance(body, dict):
        return False

    details = body.get("error", body)
    if not isinstance(details, dict):
        return False

    param = str(details.get("param") or "").strip().lower()
    if param == "response_format" or param.startswith("response_format."):
        return True

    message = str(details.get("message") or "").lower()
    if "response_format" not in message:
        return False

    code = str(details.get("code") or "").lower()
    unsupported_codes = {
        "unsupported_parameter",
        "unsupported_value",
        "unknown_parameter",
        "invalid_parameter",
    }
    unsupported_phrases = (
        "not support",
        "unsupported",
        "unknown parameter",
        "unrecognized parameter",
    )
    return code in unsupported_codes or any(
        phrase in message for phrase in unsupported_phrases
    )


def _clean_chat_text(content: str) -> str:
    """<think>-Überlegungen, BOM und einen äußeren Markdown-JSON-Codeblock entfernen."""

    # Einige Modelle (z.B. MiniMax M2.5) enthalten <think>-Überlegungen im content
    cleaned = re.sub(r'<think>[\s\S]*?</think>', '', content).strip()
    cleaned = cleaned.lstrip("\ufeff")
    cleaned = re.sub(r'^```(?:json)?\s*\n?', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\n?```\s*$', '', cleaned)
    return cleaned.strip()


def _contains_additional_json_container(content: str) -> bool:
    """True, wenn nachfolgender Text ein weiteres JSON-Objekt oder -Array enthält."""

    decoder = json.JSONDecoder()
    for match in re.finditer(r"[\[{]", content):
        try:
            value, _ = decoder.raw_decode(content[match.start():])
        except json.JSONDecodeError:
            continue
        if isinstance(value, (dict, list)):
            return True
    return False


class LLMClient:
    """LLM-Client - Unterstützt Cloud- und lokale LLMs"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        # Konfiguration basierend auf Provider laden
        llm_config = Config.get_llm_config()
        
        self.api_key = api_key or llm_config['api_key']
        self.base_url = base_url or llm_config['base_url']
        self.model = model or llm_config['model']
        self.provider = Config.LLM_PROVIDER
        
        # Für lokale LLMs: Dummy-API-Key verwenden falls nicht gesetzt
        if Config.is_local_llm() and (not self.api_key or self.api_key == 'not-needed-for-local-llm'):
            self.api_key = 'lm-studio'  # LM Studio akzeptiert beliebigen String
        
        if not self.api_key:
            raise ValueError(f"LLM_API_KEY nicht konfiguriert (Provider: {self.provider})")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def _create_completion(
        self,
        *,
        messages: List[Dict[str, str]],
        temperature: Optional[float],
        max_tokens: Optional[int],
        response_format: Optional[Dict[str, Any]],
    ) -> Any:
        """Eine rohe Chat-Completions-Anfrage über die Kompatibilitätsschicht senden."""
        extra_kwargs: Dict[str, Any] = {}
        if self.provider in ('ollama', 'lmstudio', 'local'):
            # Lokale Denk-Modelle (gemma4, qwen3.5) verbrauchen sonst das Token-Budget für Reasoning und liefern
            # leeren Inhalt; Ollama honoriert reasoning_effort auf /v1. Abschaltbar über LOCAL_LLM_REASONING=on.
            if os.environ.get('LOCAL_LLM_REASONING', 'none').lower() != 'on':
                extra_kwargs["extra_body"] = {"reasoning_effort": "none"}

        return create_chat_completion(
            self.client,
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
            **extra_kwargs,
        )
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = 4096,
        response_format: Optional[Dict] = None
    ) -> str:
        """
        Chat-Anfrage senden
        
        Args:
            messages: Nachrichtenliste
            temperature: Temperaturparameter
            max_tokens: Maximale Token-Anzahl (None = Grenze des Anbieters)
            response_format: Antwortformat (z.B. JSON-Modus)
            
        Returns:
            Modellantworttext
        """
        try:
            response = self._create_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
            )
            if not response or not response.choices:
                raise ValueError("Modell lieferte eine leere Antwort zurück (keine Choices).")
                
            message = response.choices[0].message
            if message.content is None:
                # Prüfen ob es eine Refusal gibt
                if getattr(message, 'refusal', None):
                    raise ValueError(f"Modell hat die Antwort verweigert: {message.refusal}")
                
            content = extract_chat_completion_text(response)
            return _clean_chat_text(content)
        except Exception as e:
            # Detaillierte Fehlermeldung für Debugging
            raise Exception(f"LLM-Anfrage fehlgeschlagen (Provider: {self.provider}, URL: {self.base_url}, Modell: {self.model}): {str(e)}")
    
    def chat_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: Optional[int] = 4096,
        max_attempts: int = 1,
    ) -> Dict[str, Any]:
        """
        Chat-Anfrage senden und JSON zurückgeben
        
        Args:
            messages: Nachrichtenliste
            temperature: Temperaturparameter
            max_tokens: Maximale Token-Anzahl
            max_attempts: Anzahl der Inhaltsversuche (ohne die eine Herabstufung bei
                          ausdrücklich abgelehntem JSON-Modus)
            
        Returns:
            Geparstes JSON-Objekt
        """
        if max_attempts < 1:
            raise ValueError("max_attempts muss mindestens 1 sein")

        response_format: Optional[Dict[str, str]] = {"type": "json_object"}
        request_max_tokens = max_tokens
        last_error: Optional[LLMResponseError] = None

        for attempt in range(1, max_attempts + 1):
            # Aushandeln des JSON-Modus ist getrennt von der Inhaltswiederholung: eine ausdrückliche
            # Ablehnung von response_format kostet eine Anfrage, aber keinen Inhaltsversuch.
            while True:
                try:
                    response = self._create_completion(
                        messages=messages,
                        temperature=temperature,
                        max_tokens=request_max_tokens,
                        response_format=response_format,
                    )
                except Exception as error:
                    if (
                        response_format is not None
                        and _is_response_format_unsupported(error)
                    ):
                        logger.warning(
                            "LLM-Anbieter lehnt response_format ab; "
                            "einmalige Wiederholung nur mit JSON-Anweisung im Prompt"
                        )
                        response_format = None
                        continue
                    raise
                break

            try:
                return self._parse_json_response(response)
            except LLMResponseError as error:
                last_error = error
                if attempt >= max_attempts:
                    raise

                # Eine vom Aufrufer gesetzte Token-Grenze ist die häufigste Ursache für halbes JSON.
                # Für die eine begrenzte Wiederholung entfällt sie, damit das Modelllimit gilt.
                had_token_cap = request_max_tokens is not None
                request_max_tokens = None
                logger.warning(
                    "LLM lieferte unbrauchbares JSON (finish_reason=%s); "
                    "Inhalt wird erneut generiert%s",
                    error.finish_reason or "unknown",
                    " ohne Token-Grenze" if had_token_cap else "",
                )

        if last_error is not None:  # pragma: no cover - defensive Schleifenabsicherung
            raise last_error
        raise LLMResponseError("LLM hat keine JSON-Antwort geliefert")

    @staticmethod
    def _parse_json_response(response: Any) -> Dict[str, Any]:
        """Antwort streng als JSON-Objekt lesen; abgeschnittenes JSON wird nie repariert oder ergänzt."""
        choices = getattr(response, "choices", None) or []
        if not choices:
            raise LLMResponseError("LLM lieferte keine Choices")

        choice = choices[0]
        finish_reason = getattr(choice, "finish_reason", None)
        if finish_reason == "length":
            raise LLMResponseError(
                "JSON-Ausgabe des LLM wurde an der Token-Grenze abgeschnitten",
                finish_reason=finish_reason,
            )
        if finish_reason not in {None, "stop"}:
            raise LLMResponseError(
                f"JSON-Generierung des LLM unerwartet beendet ({finish_reason})",
                finish_reason=finish_reason,
            )

        content = _clean_chat_text(extract_chat_completion_text(response))
        if not content:
            raise LLMResponseError(
                "LLM lieferte leeren JSON-Inhalt",
                finish_reason=finish_reason,
            )

        try:
            value = json.loads(content)
        except json.JSONDecodeError as strict_error:
            # Manche kompatiblen Anbieter hängen nach einem vollständigen JSON-Objekt eine kurze
            # Erklärung an. Akzeptiert wird nur ein ab dem Anfang dekodiertes Objekt.
            try:
                value, end = json.JSONDecoder().raw_decode(content)
            except json.JSONDecodeError:
                raise LLMResponseError(
                    "Ungültiges JSON-Format von LLM zurückgegeben "
                    f"(Zeile {strict_error.lineno}, Spalte {strict_error.colno})",
                    finish_reason=finish_reason,
                ) from strict_error

            trailing = content[end:].strip()
            if trailing:
                if _contains_additional_json_container(trailing):
                    raise LLMResponseError(
                        "LLM lieferte mehrere JSON-Werte",
                        finish_reason=finish_reason,
                    )
                logger.warning("Text nach einem vollständigen JSON-Objekt des LLM wird ignoriert")

        if not isinstance(value, dict):
            raise LLMResponseError(
                "JSON-Antwort des LLM muss ein JSON-Objekt auf oberster Ebene sein",
                finish_reason=finish_reason,
            )

        return value
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Testet die Verbindung zum LLM und gibt Status-Informationen zurück
        
        Returns:
            Dict mit Status, Provider, Modell und ggf. Fehlermeldung
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Say 'OK' and nothing else."}
                ],
                max_tokens=10,
                temperature=0
            )
            
            if not response or not response.choices:
                raise ValueError("Keine Antwort vom Modell erhalten (leere Choices).")
                
            content = response.choices[0].message.content
            
            return {
                "status": "ok",
                "provider": self.provider,
                "model": self.model,
                "base_url": self.base_url,
                "response": content if content is not None else "Leere Antwort"
            }
        except Exception as e:
            return {
                "status": "error",
                "provider": self.provider,
                "model": self.model,
                "base_url": self.base_url,
                "error": str(e)
            }
