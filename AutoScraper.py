# main.py

from playwright.sync_api import sync_playwright
import time
import pandas as pd
import ujson as json
import re
import os
from pathlib import Path
from utilities.logger import setup_logger
from utilities.wait_for_loader_to_disappear import wait_for_loader_to_disappear
from utilities.perform_search import perform_search
from utilities.extract_table_data import extract_table_data
from utilities.extract_directors import extract_directors
from utilities.merger import merge_data
from utilities.cleaner import cleaner
from utilities.is_website_issue import is_website_issue
import sys, os

logger = setup_logger()

def load_json_config(filename):
    """
    Always load JSON dynamically from external 'configurations' folder
    next to the .exe or the script.
    """
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    config_path = os.path.join(base_path, "configurations", filename)

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"⚠️ Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_base_path():
    """
    Returns two paths:
      - read_path: location of bundled data (works inside exe)
      - write_path: actual folder where the exe is running (for outputs/logs)
    """
    if getattr(sys, 'frozen', False):
        read_path = sys._MEIPASS
        write_path = os.path.dirname(sys.executable)
    else:
        read_path = os.path.dirname(os.path.abspath(__file__))
        write_path = read_path
    return read_path, write_path

# import sys

# def get_base_path():
#     """Handle both normal and PyInstaller (.exe) environments"""
#     if getattr(sys, 'frozen', False):
#         # Running as compiled .exe
#         return sys._MEIPASS
#     else:
#         # Running as normal script
#         return os.path.dirname(os.path.abspath(__file__))

read_path, write_path = get_base_path()
logger.info(f"Read path: {read_path}")
logger.info(f"Write path: {write_path}")

# os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.join(base_path, "ms-playwright")
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.join(read_path, "ms-playwright")


# ----------------- Director Extraction -----------------
def extract_directors_from_href(page, href_js, raw_output_folder, timeout_ms:int = 60000):
    try:
        page.evaluate(href_js)
        page.wait_for_load_state("networkidle")
        wait_for_loader_to_disappear(page, logger, timeout_ms)
        time.sleep(1)
        director_data = extract_directors(page, logger)
        logger.info("Successfully extracted director data.")
        return director_data
    except Exception as e:
        logger.error(f"⚠️ Error parsing or fetching directors: {e}", exc_info=True)
        response_text = page.content()
        if is_website_issue(response_text):
            logger.info("Website crashed, wait and retry later.")
        else:
            logger.info("Website response looks fine, wait and retry later.")
        return []

# ----------------- Main Run -----------------
def run(date, state, defaulters_type, raw_output_folder, timeout_ms:int = 60000):    
    cibil_link_files = []
    logger.info(f'Running automation for State: {state}, Date: {date}, Defaulters type: {defaulters_type}')
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=200)
        context = browser.new_context()
        page = context.new_page()
        logger.info("Browser launched.")

        page.goto("https://suit.cibil.com/", timeout=timeout_ms, wait_until="load")
        logger.info("Page loaded.")

        # perform_search(page, date, state)
        pagination_limit = perform_search(page, logger, date, state, defaulters_type, timeout_ms)
        logger.info(f"Pagination limit: {pagination_limit}")

        # files_in_parent = os.listdir(raw_output_folder)
        # existing_files_for_state = [f for f in files_in_parent if state in f and f.endswith(".xlsx")]
        existing_files_for_state = [
            os.path.join(raw_output_folder, f)
            for f in os.listdir(raw_output_folder)
            if state.lower() in f.lower() and f.endswith(".xlsx")
        ]

        if existing_files_for_state and len(existing_files_for_state) == int(pagination_limit):
            logger.info(f"Raw Data for {state} already exists. Skipping raw table extraction.")
            cibil_link_files = existing_files_for_state.copy()
        
        else:
            for i in range(1, int(pagination_limit)+1):
                page_no = i
                if any(f'page_{page_no}' in f for f in existing_files_for_state):
                    logger.info(f"Data for {state}, page {page_no} already exists. Skipping page extraction.")
                    next_button = page.locator('td#next_pagingDiv')
                    # Check if it is enabled
                    if 'ui-state-disabled' not in next_button.get_attribute('class'):
                        next_button.click()
                        time.sleep(0.5)
                        # Wait for loader to appear and then disappear
                        try:
                            loader = page.locator('div#load_projectTable')
                            loader.wait_for(state='visible', timeout=timeout_ms)  # wait if it appears
                        except:
                            pass  # loader may not appear sometimes
                        page.wait_for_load_state("networkidle")
                        time.sleep(1)
                    else:
                        logger.info("▶ Next button is disabled, reached last page.")
                    # page.locator('td#next_pagingDiv').click()
                    page.wait_for_load_state("networkidle")
                    time.sleep(2)
                    continue
                
                cibil_df = extract_table_data(page, logger, date, defaulters_type, state, page_no, cibil_link_files, raw_output_folder, timeout_ms)
                if cibil_df.empty:
                    logger.info(f"No data for {state}, skipping director extraction")
                    continue

                next_button = page.locator('td#next_pagingDiv')
                # Check if it is enabled
                if 'ui-state-disabled' not in next_button.get_attribute('class'):
                    next_button.click()
                    # Wait for loader to appear and then disappear
                    try:
                        loader = page.locator('div#load_projectTable')
                        loader.wait_for(state='visible', timeout=timeout_ms)  # wait if it appears
                    except:
                        pass  # loader may not appear sometimes
                    page.wait_for_load_state("networkidle")
                    time.sleep(1)
                else:
                    logger.info("▶ Next button is disabled, reached last page.")
                # page.locator('td#next_pagingDiv').click()
                page.wait_for_load_state("networkidle")
                time.sleep(2)

        # ----------------- Extract directors row by row -----------------
        state_files = [
            os.path.join(raw_output_folder, f)
            for f in os.listdir(raw_output_folder)
            if f.lower().endswith(".xlsx") and state.lower() in f.lower()
        ]
        if not state_files:
            logger.warning(f"⚠️ No raw Excel files found for state: {state}")
            return
        
        logger.info(f"Found {len(state_files)} raw Excel files for {state}")

        for i, file_name in enumerate(state_files):
            df_for_director_fetch = pd.read_excel(file_name)
            if "directors_data" not in df_for_director_fetch.columns:
                df_for_director_fetch["directors_data"] = [[] for _ in range(len(df_for_director_fetch))]
            if "directors_presence" not in df_for_director_fetch.columns:
                df_for_director_fetch["directors_presence"] = "not fetched"

            # df_for_director_fetch["directors_data"] = [[] for _ in range(len(df_for_director_fetch))]
            for idx, row in df_for_director_fetch.iterrows():
                if str(df_for_director_fetch.at[idx, "directors_presence"]).lower().strip() == 'fetched':
                # if df_for_director_fetch.at[idx, "directors_presence"].lower() == 'fetched':
                    logger.info(f"Directors already extracted for row {idx+1}, skipping...")
                    continue
                href = row.get("directorName_href", "")
                if isinstance(href, str) and href.startswith("javascript:getDirctorList"):
                    logger.info(f"▶ Extracting directors for row {idx+1}: {row.get('borrowerName','')}")
                    # if df_for_director_fetch.at[idx, "directors_presence"] == 1:
                    directors = extract_directors_from_href(page, href, raw_output_folder, timeout_ms)
                    df_for_director_fetch.at[idx, "directors_data"] = directors
                    df_for_director_fetch.at[idx, "directors_presence"] = 'fetched'

                    try:
                        page.go_back(timeout=60000)
                        page.wait_for_load_state("networkidle")
                        wait_for_loader_to_disappear(page, logger, timeout_ms)
                        time.sleep(1)
                    except Exception:
                        logger.info("⚠️ Could not navigate back, reloading page...")
                        # Reload the page and re-perform the search to restore state
                        page.reload()
                        page.wait_for_load_state("networkidle")
                        wait_for_loader_to_disappear(page, logger, timeout_ms)
                        time.sleep(1)
                        logger.info("🔄 Page reloaded successfully.")
                
                if (idx+1) % 5 == 0:
                    df_for_director_fetch.to_excel(file_name, index=False)
                    logger.info(f"Checkpoint saved at row {idx+1} for {file_name}")

            df_for_director_fetch.to_excel(file_name, index=False)
            logger.info(f"✅ Updated raw file saved with director info → {file_name}")

        browser.close()

# ----------------- Entry Point -----------------
def data_search():
    # # When running from .exe, this ensures it finds the bundled browsers
    # os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.join(os.getcwd(), "ms-playwright")

    # with open("configurations/search_details.json", "r") as f:
    # with open(os.path.join(base_path, "configurations", "search_details.json"), "r") as f:
    # with open(os.path.join(read_path, "configurations", "search_details.json"), "r") as f:
    #     search_details = json.load(f)
    
    search_details = load_json_config("search_details.json")
    state_details = load_json_config("state_details.json")
    date = search_details.get("date", "31-01-25")
    defaulters_type = search_details.get("defaulters_type", "1 crore")
    state_selection = search_details.get("state_selection", "state")
    timeout_seconds = int(search_details.get("timeout(seconds)", 60))
    # logger.info(f'State selection configuration: {state_selection}')
    logger.info(f'Selected Configurations: \nState type: {state_selection}, \nDefaulters type: {defaulters_type}, \nDate: {date}, \nTimeout: {timeout_seconds} seconds')
    timeout_seconds = timeout_seconds * 1000 # conversion to milliseconds

    # with open('configurations/state_details.json', 'r') as ff:
    # with open(os.path.join(base_path, "configurations", "state_details.json"), "r") as ff:
    # with open(os.path.join(read_path, "configurations", "state_details.json"), "r") as ff:
    #     state_details = json.load(ff)
    
    all_states = set(state_details.get("all_states", []))
    selected_states = state_details.get(state_selection, ["GOA"])
    # logger.info(f'Selected states: {all_states}')
    logger.info(f'All States: {all_states}')
    logger.info(f'Selected States: {selected_states}')

    # Filter only valid states
    valid_states = []
    for state in selected_states:
        if state in all_states:
            valid_states.append(state)
        else:
            logger.warning(f"❌ Invalid state skipped: {state}")
    
    if not valid_states:
        logger.error("❌ No valid states to process. Exiting.")
        return
    
    logger.info(f"▶ Starting batch search for Date: {date}")
    
    # Folder creation for output
    defaulters_type = defaulters_type.strip().lower().replace(" ", "_").replace("-", "_").replace(">", "gt_").replace("<", "lt_")
    # safe_def_type = re.sub(r'[^\w]+', '_', defaulters_type)
    # base_output_dir = Path("fetched_data")
    # base_output_dir = Path(os.path.join(base_path, "fetched_data"))
    base_output_dir = Path(os.path.join(write_path, "fetched_data"))
    raw_output_folder = base_output_dir / "raw" / f'cibil_data_{defaulters_type}_{date}_for_{state_selection}'
    # final_output_folder = base_output_dir / "final" / f'cibil_data_with_directors_{safe_def_type}_{date}_for_{state_selection}'

    os.makedirs(raw_output_folder, exist_ok=True)
    # os.makedirs(final_output_folder, exist_ok=True)
    
    for state in valid_states:
        try:
            run(date, state, defaulters_type, raw_output_folder, timeout_seconds)
        except Exception as e:
            logger.error(f"❌ Error for {state}: {e}")
            continue

if __name__ == "__main__":
    logger.info("▶ Running script...")
    logger.info("Running script...")
    data_search()
    merge_data(logger)
    cleaner(logger)
