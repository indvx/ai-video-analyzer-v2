import logging
from app.core.config import settings
import os

# Centralized log file path where all application events and errors get appended
LOG_FILE = os.path.join(settings.log_file_dir, "app.log")


def setup_logger(file: str = __name__):
    """Sets up a logger instance that outputs to both console (stdout) and a persistent log file.
    
    Accepts the module `__name__` so log entries clearly show where the message originated.
    """
    logger = logging.getLogger(file)
    logger.setLevel(logging.DEBUG)

    # StreamHandler allows real-time terminal monitoring during development and container runs
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    
    # Configure root logger to write utf-8 encoded files (safely handles unicode video titles and prompts)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )

    # Apply standard timestamped format for individual module loggers
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger
