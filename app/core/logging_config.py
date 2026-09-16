import logging
import os

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "app.log")

_session_logged = False


def configure_logging():
    global _session_logged

    os.makedirs(LOG_DIR, exist_ok=True)

    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            handlers=[
                logging.FileHandler(LOG_FILE, mode="a"),
                logging.StreamHandler(),
            ],
        )

    if not _session_logged:
        logging.getLogger(__name__).info("=== New application session started ===")
        _session_logged = True