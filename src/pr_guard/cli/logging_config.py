# pr_guard/utils/logger.py
import logging


def setup_logger():
    logger = logging.getLogger("pr_guard")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger  # prevent duplicate handlers on reload

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    # File (persistent)
    file_handler = None

    try:
        file_handler = logging.FileHandler(".pr_guard/pr_guard.log")
        file_handler.setLevel(logging.ERROR)
        file_handler.setFormatter(formatter)
    except Exception:
        pass

    # Console handler (developer visibility)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    if file_handler:
        logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Uvicorn logging hygiene
    logging.getLogger("uvicorn").setLevel(logging.WARNING)  # framework noise
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)  # errors + startup
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)  # HTTP requests

    return logger
