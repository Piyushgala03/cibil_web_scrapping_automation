# logger.py

import logging
import time
from pathlib import Path

def setup_logger():
    current_date = time.strftime("%Y-%m-%d")

    # Create folder path: logs/<date>/
    log_dir = Path("logs") / current_date
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create log file name inside date folder
    log_filename = log_dir / f"cibil_log_{time.strftime('%Y-%m-%d_%H-%M-%S')}.log"

    logging.basicConfig(
        filename=log_filename,
        level=logging.DEBUG, # capture DEBUG, INFO, WARNING, ERROR, CRITICAL
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    return logging
