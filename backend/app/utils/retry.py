"""
API-Aufrufwiederholungsmechanismus
Verarbeitet die Wiederholungslogik für externe API-Aufrufe wie LLMs
"""

import time
import random
import functools
from typing import Callable, Any, Optional, Type, Tuple
from ..utils.logger import get_logger

logger = get_logger('mirofish.retry')


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 30.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None
):
    """
    Retry-Dekorator mit exponentiellem Backoff
    
    Args:
        max_retries: Maximale Anzahl der Wiederholungen
        initial_delay: Initiale Verzögerung (Sekunden)
        max_delay: Maximale Verzögerung (Sekunden)
        backoff_factor: Backoff-Faktor
        jitter: Zufälliges Jitter hinzufügen
        exceptions: Ausnahmearten, die wiederholt werden sollen
        on_retry: Callback-Funktion bei Wiederholung (exception, retry_count)
    
    Usage:
        @retry_with_backoff(max_retries=3)
        def call_llm_api():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            delay = initial_delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(f"Funktion {func.__name__} schlägt nach {max_retries} Wiederholungen weiterhin fehl: {str(e)}")
                        raise
                    
                    # Berechne Verzögerung
                    current_delay = min(delay, max_delay)
                    if jitter:
                        current_delay = current_delay * (0.5 + random.random())
                    
                    logger.warning(
                        f"Funktion {func.__name__} Versuch {attempt + 1} fehlgeschlagen: {str(e)}, "
                        f"Wiederholung nach {current_delay:.1f} Sekunden..."
                    )
                    
                    if on_retry:
                        on_retry(e, attempt + 1)
                    
                    time.sleep(current_delay)
                    delay *= backoff_factor
            
            raise last_exception
        
        return wrapper
    return decorator


def retry_with_backoff_async(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 30.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None
):
    """
    Retry-Dekorator für die asynchrone Version
    """
    import asyncio
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            delay = initial_delay
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                    
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(f"Asynchrone Funktion {func.__name__} nach {max_retries} Wiederholungen weiterhin fehlgeschlagen: {str(e)}")
                        raise
                    
                    current_delay = min(delay, max_delay)
                    if jitter:
                        current_delay = current_delay * (0.5 + random.random())
                    
                    logger.warning(
                        f"Asynchrone Funktion {func.__name__} Versuch {attempt + 1} fehlgeschlagen: {str(e)}, "
                        f"Wiederholung nach {current_delay:.1f} Sekunden..."
                    )
                    
                    if on_retry:
                        on_retry(e, attempt + 1)
                    
                    await asyncio.sleep(current_delay)
                    delay *= backoff_factor
            
            raise last_exception
        
        return wrapper
    return decorator


class RetryableAPIClient:
    """
    Retry-fähige API-Client-Kapselung
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 30.0,
        backoff_factor: float = 2.0
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
    
    def call_with_retry(
        self,
        func: Callable,
        *args,
        exceptions: Tuple[Type[Exception], ...] = (Exception,),
        **kwargs
    ) -> Any:
        """
        Führt Funktionsaufruf aus und wiederholt bei Fehler
        
        Args:
            func: Zu aufrufende Funktion
            *args: Funktionsparameter
            exceptions: Ausnahmearten für Retry
            **kwargs: Funktionsschlüsselparameter
            
        Returns:
            Funktionsrückgabewert
        """
        last_exception = None
        delay = self.initial_delay
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
                
            except exceptions as e:
                last_exception = e
                
                if attempt == self.max_retries:
                    logger.error(f"API-Aufruf nach {self.max_retries} Wiederholungen fehlgeschlagen: {str(e)}")
                    raise
                
                current_delay = min(delay, self.max_delay)
                current_delay = current_delay * (0.5 + random.random())
                
                logger.warning(
                    f"API-Aufruf Versuch {attempt + 1} fehlgeschlagen: {str(e)}, "
                    f"Wiederholung nach {current_delay:.1f} Sekunden..."
                )
                
                time.sleep(current_delay)
                delay *= self.backoff_factor
        
        raise last_exception
    
    def call_batch_with_retry(
        self,
        items: list,
        process_func: Callable,
        exceptions: Tuple[Type[Exception], ...] = (Exception,),
        continue_on_failure: bool = True
    ) -> Tuple[list, list]:
        """
        Batch-Aufruf mit Einzelwiederholung für jeden fehlgeschlagenen Punkt
        
        Args:
            items: Liste der zu verarbeitenden Elemente
            process_func: Verarbeitungsfunktion, nimmt ein einzelnes Item als Parameter
            exceptions: Ausnahmearten, die wiederholt werden müssen
            continue_on_failure: Ob nach einem Fehler einzelner Elemente mit anderen fortgefahren wird
            
        Returns:
            (Liste der Erfolge, Liste der Fehler)
        """
        results = []
        failures = []
        
        for idx, item in enumerate(items):
            try:
                result = self.call_with_retry(
                    process_func,
                    item,
                    exceptions=exceptions
                )
                results.append(result)
                
            except Exception as e:
                logger.error(f"Verarbeitung von Element {idx + 1} fehlgeschlagen: {str(e)}")
                failures.append({
                    "index": idx,
                    "item": item,
                    "error": str(e)
                })
                
                if not continue_on_failure:
                    raise
        
        return results, failures

