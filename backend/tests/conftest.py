"""Die Aufräum-Tests brauchen nur Config und cleanup.

app/__init__.py zieht Flask, app/services/__init__.py den ganzen Dienststapel.
Beides läuft hier nicht: die Pakete werden leer vorgemerkt, damit die echten
__init__-Dateien nicht ausgeführt werden.
"""
import sys
import types
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1]


def _stub(name: str, path: Path) -> None:
    if name in sys.modules:
        return
    module = types.ModuleType(name)
    module.__path__ = [str(path)]
    module.__package__ = name
    sys.modules[name] = module


_stub("app", _BACKEND / "app")
_stub("app.services", _BACKEND / "app" / "services")
_stub("app.utils", _BACKEND / "app" / "utils")
