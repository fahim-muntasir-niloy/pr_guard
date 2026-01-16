# pr_guard/utils/logger.py
import logging


def setup_logger():
    logger = logging.getLogger("pr_guard")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger  # prevent duplicate handlers on reload

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    # File (persistent)
    file_handler = logging.FileHandler("pr_guard.log")
    file_handler.setLevel(logging.ERROR)
    file_handler.setFormatter(formatter)

    # Console (clean)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Silence uvicorn noise
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    return logger
