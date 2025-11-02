import logging
import time
import os
from pathlib import Path


def setup_logger():
    # ✅ Detect correct base path even in PyInstaller Onefile mode
    if getattr(os, 'frozen', False):
        # When running as .exe, use the folder containing the EXE
        base_path = Path(os.path.dirname(os.path.abspath(os.sys.executable)))
    else:
        # When running as script, use the folder containing this file
        base_path = Path(os.path.dirname(os.path.abspath(__file__)))

    # ✅ In case the code is executed from temp (_MEI...), go one level up
    # This ensures logs go beside your main.exe
    if "_MEI" in str(base_path):
        base_path = Path(os.getcwd())

    current_date = time.strftime("%Y-%m-%d")
    log_dir = base_path / "logs" / current_date
    log_dir.mkdir(parents=True, exist_ok=True)

    log_filename = log_dir / f"cibil_log_{time.strftime('%Y-%m-%d_%H-%M-%S')}.log"

    # logging.basicConfig(
    #     filename=log_filename,
    #     level=logging.INFO,
    #     format="%(asctime)s - %(levelname)s - %(message)s"
    # )

    # logger.info(f"✅ Logging initialized at: {log_filename}")
    # return logging
    # ✅ Create logger instance
    logger = logging.getLogger("CIBILLogger")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()  # Prevent duplicate handlers on rerun

    # --- File Handler ---
    file_handler = logging.FileHandler(log_filename, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(file_formatter)

    # --- Console Handler ---
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("▶ %(message)s")  # cleaner console output
    console_handler.setFormatter(console_formatter)

    # --- Add Handlers ---
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info(f"Logging initialized at: {log_filename}")
    return logger