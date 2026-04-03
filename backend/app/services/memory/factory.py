"""
Factory für Memory-Provider
Erstellt die passende Provider-Instanz basierend auf der Konfiguration
"""

from typing import Optional
from .base import MemoryProvider
from .zep_provider import ZepMemoryProvider
from .obsidian_provider import ObsidianMemoryProvider
from .hybrid_provider import HybridMemoryProvider
from ...config import Config
from ...utils.logger import get_logger

logger = get_logger('mirofish.memory.factory')

class MemoryFactory:
    """Erstellt Memory-Provider Instanzen"""
    
    _instance: Optional[MemoryProvider] = None
    
    @classmethod
    def get_provider(cls, provider_type: Optional[str] = None) -> MemoryProvider:
        """
        Gibt eine Singleton-Instanz des konfigurierten Providers zurück
        """
        if cls._instance is None:
            p_type = (provider_type or Config.MEMORY_PROVIDER).lower()
            
            if p_type == 'zep':
                logger.info("Initialisiere ZepMemoryProvider")
                cls._instance = ZepMemoryProvider()
            elif p_type == 'obsidian':
                logger.info("Initialisiere ObsidianMemoryProvider")
                cls._instance = ObsidianMemoryProvider()
            elif p_type == 'hybrid':
                logger.info("Initialisiere HybridMemoryProvider")
                cls._instance = HybridMemoryProvider()
            else:
                logger.warning(f"Unbekannter Provider-Typ '{p_type}', nutze Zep als Fallback")
                cls._instance = ZepMemoryProvider()
                
        return cls._instance

    @classmethod
    def reset(cls):
        """Setzt die Singleton-Instanz zurück (z.B. für Tests)"""
        cls._instance = None
