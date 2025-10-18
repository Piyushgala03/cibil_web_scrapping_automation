# logger.py

# import logging
# import time
# from pathlib import Path

# def setup_logger():
#     current_date = time.strftime("%Y-%m-%d")

#     # Create folder path: logs/<date>/
#     log_dir = Path("logs") / current_date
#     log_dir.mkdir(parents=True, exist_ok=True)

#     # Create log file name inside date folder
#     log_filename = log_dir / f"cibil_log_{time.strftime('%Y-%m-%d_%H-%M-%S')}.log"

#     logging.basicConfig(
#         filename=log_filename,
#         level=logging.DEBUG, # capture DEBUG, INFO, WARNING, ERROR, CRITICAL
#         format="%(asctime)s - %(levelname)s - %(message)s"
#     )
#     return logging


# import logging
# import time
# import os
# from pathlib import Path


# def setup_logger():
#     # ✅ Detect base path for both script and PyInstaller EXE
#     if getattr(os, 'frozen', False):
#         base_path = os.path.dirname(os.path.abspath(os.sys.executable))
#     else:
#         base_path = os.path.dirname(os.path.abspath(__file__))

#     current_date = time.strftime("%Y-%m-%d")

#     # ✅ Logs inside <base_path>/logs/<date>/
#     log_dir = Path(base_path) / "logs" / current_date
#     log_dir.mkdir(parents=True, exist_ok=True)

#     # ✅ Create log file name
#     log_filename = log_dir / f"cibil_log_{time.strftime('%Y-%m-%d_%H-%M-%S')}.log"

#     logging.basicConfig(
#         filename=log_filename,
#         level=logging.DEBUG,
#         format="%(asctime)s - %(levelname)s - %(message)s"
#     )

#     return logging


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

    logging.basicConfig(
        filename=log_filename,
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    print(f"✅ Logging initialized at: {log_filename}")
    return logging
