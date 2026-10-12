"""
Log-Konfigurationsmodul
Bietet ein einheitliches Log-Management mit gleichzeitiger Ausgabe an Konsole und Datei
"""

import os
import sys
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler


def _ensure_utf8_stdout():
    """
    Stelle sicher, dass stdout/stderr UTF-8 kodiert sind
    Behebt Probleme mit chinesischen Schriftzeichen in der Windows-Konsole
    """
    if sys.platform == 'win32':
        # Konfiguriere unter Windows die Standardausgabe neu als UTF-8
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')


# Log-Verzeichnis
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')


def setup_logger(name: str = 'mirofish', level: int = logging.DEBUG) -> logging.Logger:
    """
    Logger konfigurieren
    
    Args:
        name: Logger-Name
        level: Log-Level
        
    Returns:
        Konfigurierter Logger
    """
    # Stelle sicher, dass das Log-Verzeichnis existiert
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # Erstelle Logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Verhindert die Weiterleitung von Logs an den Root-Logger, um doppelte Ausgaben zu vermeiden
    logger.propagate = False
    
    # Wenn bereits ein Handler vorhanden ist, nicht erneut hinzufügen
    if logger.handlers:
        return logger
    
    # Log-Format
    detailed_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # 1. Datei-Handler - Detaillierte Logs (nach Datum benannt, mit Rotation)
    log_filename = datetime.now().strftime('%Y-%m-%d') + '.log'
    file_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, log_filename),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    
    # 2. Konsolen-Handler - Kurze Logs (INFO und höher)
    # Sicherstellen der UTF-8-Kodierung unter Windows, um chinesische Glyphenfehler zu vermeiden
    _ensure_utf8_stdout()
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    
    # Handler hinzufügen
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str = 'mirofish') -> logging.Logger:
    """
    Logger abrufen (falls nicht vorhanden, erstellen)
    
    Args:
        name: Logger-Name
        
    Returns:
        Logger-Instanz
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger


# Erstellen des Standard-Loggers
logger = setup_logger()


# Bequeme Methode
def debug(msg, *args, **kwargs):
    logger.debug(msg, *args, **kwargs)

def info(msg, *args, **kwargs):
    logger.info(msg, *args, **kwargs)

def warning(msg, *args, **kwargs):
    logger.warning(msg, *args, **kwargs)

def error(msg, *args, **kwargs):
    logger.error(msg, *args, **kwargs)

def critical(msg, *args, **kwargs):
    logger.critical(msg, *args, **kwargs)

