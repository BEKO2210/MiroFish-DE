"""
LLM-Client-Wrapper
Einheitliche Verwendung des OpenAI-Formats
Unterstützt: OpenAI, LM Studio, Ollama und andere OpenAI-kompatible APIs
"""

import json
import re
from typing import Optional, Dict, Any, List
from openai import OpenAI

from ..config import Config


class LLMClient:
    """LLM客户端 - Unterstützt Cloud- und lokale LLMs"""
    
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
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[Dict] = None
    ) -> str:
        """
        Chat-Anfrage senden
        
        Args:
            messages: Nachrichtenliste
            temperature: Temperaturparameter
            max_tokens: Maximale Token-Anzahl
            response_format: Antwortformat (z.B. JSON-Modus)
            
        Returns:
            Modellantworttext
        """
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        if response_format:
            kwargs["response_format"] = response_format
        
        try:
            response = self.client.chat.completions.create(**kwargs)
            if not response or not response.choices:
                raise ValueError("Modell lieferte eine leere Antwort zurück (keine Choices).")
                
            content = response.choices[0].message.content
            if content is None:
                # Prüfen ob es eine Refusal oder Tool-Calls gibt
                if hasattr(response.choices[0].message, 'refusal') and response.choices[0].message.refusal:
                    raise ValueError(f"Modell hat die Antwort verweigert: {response.choices[0].message.refusal}")
                content = ""
                
            # Einige Modelle (z.B. MiniMax M2.5) enthalten <think>-Überlegungen im content, diese müssen entfernt werden
            content = re.sub(r'<think>[\s\S]*?</think>', '', content).strip()
            return content
        except Exception as e:
            # Detaillierte Fehlermeldung für Debugging
            raise Exception(f"LLM-Anfrage fehlgeschlagen (Provider: {self.provider}, URL: {self.base_url}, Modell: {self.model}): {str(e)}")
    
    def chat_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """
        Chat-Anfrage senden und JSON zurückgeben
        
        Args:
            messages: Nachrichtenliste
            temperature: Temperaturparameter
            max_tokens: Maximale Token-Anzahl
            
        Returns:
            Geparstes JSON-Objekt
        """
        response = self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"}
        )
        # Markdown-Codeblock-Markierungen bereinigen
        cleaned_response = response.strip()
        cleaned_response = re.sub(r'^```(?:json)?\s*\n?', '', cleaned_response, flags=re.IGNORECASE)
        cleaned_response = re.sub(r'\n?```\s*$', '', cleaned_response)
        cleaned_response = cleaned_response.strip()

        try:
            return json.loads(cleaned_response)
        except json.JSONDecodeError:
            raise ValueError(f"Ungültiges JSON-Format von LLM zurückgegeben: {cleaned_response}")
    
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
