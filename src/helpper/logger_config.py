import logging
import json
from rich.logging import RichHandler

class SmartLogger(logging.Logger):
    def info(self, msg, *args, **kwargs):
        msg = self._normalize_message(msg)
        super().info(msg, *args, stacklevel=2, **kwargs)

    def error(self, msg, *args, **kwargs):
        msg = self._normalize_message(msg)
        super().error(msg, *args, stacklevel=2, **kwargs)

    def warning(self, msg, *args, **kwargs):
        msg = self._normalize_message(msg)
        super().warning(msg, *args, stacklevel=2, **kwargs)

    def _normalize_message(self, msg):
        import sqlite3
        if isinstance(msg, sqlite3.Row):
            msg = dict(msg)
        elif isinstance(msg, (dict, list)):
            msg = json.dumps(msg, ensure_ascii=False, indent=2)
        return msg

# --- Global logger config ---
logging.setLoggerClass(SmartLogger)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[RichHandler(rich_tracebacks=True)]
)

logger = logging.getLogger("DataWarehouse")
