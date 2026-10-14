"""Kindprozesse der Tests laden das hier über PYTHONPATH, bevor das Skript läuft."""
import os

if os.environ.get("MIROFISH_NET_GUARD", "").strip().lower() in {"1", "true", "yes", "on"}:
    import net_guard

    net_guard.install()
