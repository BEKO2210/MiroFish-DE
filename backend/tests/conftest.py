"""Hermetische Tests: keine Projekt-.env, kein echtes Ollama, kein Zep.

MIROFISH_SKIP_DOTENV steht, bevor irgendein Test app importiert. Die
Autouse-Fixture räumt Dienstervariablen vor jedem Test erneut ab.

app/__init__.py zieht Flask, app/services/__init__.py den ganzen Dienststapel.
Beides läuft hier nicht: die Pakete werden leer vorgemerkt, damit die echten
__init__-Dateien nicht ausgeführt werden.
"""
import os
import sys
import types
from pathlib import Path

import pytest

_GUARD_DIR = Path(__file__).resolve().parent / "_hermetic_site"
if str(_GUARD_DIR) not in sys.path:
    sys.path.insert(1, str(_GUARD_DIR))

os.environ["MIROFISH_SKIP_DOTENV"] = "1"
os.environ["MIROFISH_NET_GUARD"] = "1"

import net_guard

net_guard.scrub(os.environ)
net_guard.install()

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


@pytest.fixture(autouse=True)
def hermetische_umgebung():
    net_guard.scrub(os.environ)
    net_guard.install()
    yield
