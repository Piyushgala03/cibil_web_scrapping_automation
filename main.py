# main.py

from playwright.sync_api import sync_playwright
import time
import pandas as pd
import ujson as json
import re
import logging
import os
from pathlib import Path
from utilities.logger import setup_logger
from utilities.wait_for_loader_to_disappear import wait_for_loader_to_disappear
from utilities.perform_search import perform_search
from utilities.extract_table_data import extract_table_data
from utilities.extract_directors import extract_directors
from utilities.merger import merge_data
from utilities.cleaner import cleaner
import sys, os


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
print(f"Read path: {read_path}")
print(f"Write path: {write_path}")

# os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.join(base_path, "ms-playwright")
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.join(read_path, "ms-playwright")

logging = setup_logger()

# ----------------- Director Extraction -----------------
def extract_directors_from_href(page, href_js, raw_output_folder, final_output_folder):
    try:
        # js_code = href_js.replace("javascript:", "")
        # page.evaluate(js_code)
        page.evaluate(href_js)
        page.wait_for_load_state("networkidle")
        wait_for_loader_to_disappear(page, logging)
        time.sleep(1)
        director_data = extract_directors(page, logging)
        logging.info("Successfully extracted director data.")
        return director_data
    except Exception as e:
        print(f"⚠️ Error parsing or fetching directors: {e}")
        logging.error(f"Error parsing or fetching directors: {e}", exc_info=True)
        return []

# ----------------- Main Run -----------------
def run(date, state, defaulters_type, raw_output_folder, final_output_folder):    
    cibil_link_files = []
    print("▶ Starting Playwright...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=200)
        context = browser.new_context()
        page = context.new_page()
        print("✅ Browser launched.")
        logging.info("Browser launched.")

        page.goto("https://suit.cibil.com/", timeout=60000, wait_until="load")
        print("✅ Page loaded.")
        logging.info("Page loaded.")

        # perform_search(page, date, state)
        pagination_limit = perform_search(page, logging, date, state, defaulters_type)
        logging.info(f"Pagination limit = {pagination_limit}")

        if pagination_limit > 1:
            print(f"⚠️ More than 1000 rows found ({pagination_limit*1000} total).")

            for i in range(1, int(pagination_limit)+1):
                page_no = i
                output_file, cibil_df = extract_table_data(page, logging, date, state, page_no, cibil_link_files, raw_output_folder)
                if cibil_df.empty:
                    logging.info(f"No data for {state}, skipping director extraction")
                    continue

                next_button = page.locator('td#next_pagingDiv')
                # Check if it is enabled
                if 'ui-state-disabled' not in next_button.get_attribute('class'):
                    next_button.click()
                    # Wait for loader to appear and then disappear
                    try:
                        loader = page.locator('div#load_projectTable')
                        loader.wait_for(state='visible', timeout=5000)  # wait if it appears
                    except:
                        pass  # loader may not appear sometimes
                    page.wait_for_load_state("networkidle")
                    time.sleep(1)
                else:
                    print("▶ Next button is disabled, reached last page.")
                # page.locator('td#next_pagingDiv').click()
                page.wait_for_load_state("networkidle")
                time.sleep(2)


            # ----------------- Extract directors row by row -----------------
            for i, file_name in enumerate(cibil_link_files):
                df_for_director_fetch = pd.read_excel(file_name)
                df_for_director_fetch["directors_data"] = [[] for _ in range(len(df_for_director_fetch))]
                for idx, row in df_for_director_fetch.iterrows():
                    href = row.get("directorName_href", "")
                    if isinstance(href, str) and href.startswith("javascript:getDirctorList"):
                        print(f"▶ Extracting directors for row {idx+1}: {row.get('borrowerName','')}")
                        directors = extract_directors_from_href(page, href, raw_output_folder, final_output_folder)
                        df_for_director_fetch.at[idx, "directors_data"] = directors

                        try:
                            page.go_back(timeout=60000)
                            page.wait_for_load_state("networkidle")
                            wait_for_loader_to_disappear(page, logging)
                            time.sleep(1)
                        except Exception:
                            print("⚠️ Could not navigate back, reloading page...")
                            # Reload the page and re-perform the search to restore state
                            page.reload()
                            page.wait_for_load_state("networkidle")
                            wait_for_loader_to_disappear(page, logging)
                            time.sleep(1)
                            print("🔄 Page reloaded successfully.")

                timestamp = time.strftime("%Y%m%d_%H%M%S")
                df_for_director_fetch['State'] = state
                output_with_directors = f"cibil_data_with_directors_{date}_{state}_state_page_{i+1}_{timestamp}.xlsx"
                final_output_with_directors_path = os.path.join(final_output_folder, output_with_directors)
                df_for_director_fetch.to_excel(final_output_with_directors_path, index=False)
                # df_for_director_fetch.to_excel(output_with_directors, index=False)
            
            print(f"💾 Saved enriched data to {final_output_with_directors_path}")

        else:
            page_no = 1
            output_file, cibil_df = extract_table_data(page, logging, date, state, page_no, cibil_link_files, raw_output_folder)
            cibil_df["directors_data"] = [[] for _ in range(len(cibil_df))]
            # ----------------- Extract directors row by row -----------------
            for idx, row in cibil_df.iterrows():
                href = row.get("directorName_href", "")
                if isinstance(href, str) and href.startswith("javascript:getDirctorList"):
                    print(f"▶ Extracting directors for row {idx+1}: {row.get('borrowerName','')}")
                    directors = extract_directors_from_href(page, href, raw_output_folder, final_output_folder)
                    cibil_df.at[idx, "directors_data"] = directors

                    try:
                        page.go_back(timeout=60000)
                        page.wait_for_load_state("networkidle")
                        wait_for_loader_to_disappear(page, logging)
                        time.sleep(1)
                    except Exception:
                        print("⚠️ Could not navigate back, reloading page...")
                        # Reload the page and re-perform the search to restore state
                        page.reload()
                        page.wait_for_load_state("networkidle")
                        wait_for_loader_to_disappear(page, logging)
                        time.sleep(1)
                        print("🔄 Page reloaded successfully.")

            timestamp = time.strftime("%Y%m%d_%H%M%S")
            cibil_df['State'] = state
            output_with_directors = f"cibil_data_with_directors_{date}_{state}_state_page_{page_no}_{timestamp}.xlsx"
            final_output_with_directors_path = os.path.join(final_output_folder, output_with_directors)
            cibil_df.to_excel(final_output_with_directors_path, index=False)
            print(f"💾 Saved enriched data to {final_output_with_directors_path}")

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
    print(f'State selection configuration: {state_selection}')

    # with open('configurations/state_details.json', 'r') as ff:
    # with open(os.path.join(base_path, "configurations", "state_details.json"), "r") as ff:
    # with open(os.path.join(read_path, "configurations", "state_details.json"), "r") as ff:
    #     state_details = json.load(ff)
    
    all_states = set(state_details.get("all_states", []))
    states = state_details.get(state_selection, ["Delhi"])
    print(f'Selected states: {all_states}')

    # Filter only valid states
    valid_states = []
    for state in states:
        if state in all_states:
            valid_states.append(state)
        else:
            print(f"❌ Invalid state skipped: {state}")
            logging.warning(f"Invalid state skipped: {state}")
    
    if not valid_states:
        print("❌ No valid states to process. Exiting.")
        logging.error("No valid states to process. Exiting.")
        return
    
    print(f"▶ Starting batch search for date: {date}")
    logging.info(f"Starting batch search for date: {date}")
    
    # Folder creation for output
    safe_def_type = re.sub(r'[^\w]+', '_', defaulters_type)
    # base_output_dir = Path("fetched_data")
    # base_output_dir = Path(os.path.join(base_path, "fetched_data"))
    base_output_dir = Path(os.path.join(write_path, "fetched_data"))
    raw_output_folder = base_output_dir / "raw" / f'cibil_data_{safe_def_type}_{date}_for_{state_selection}'
    final_output_folder = base_output_dir / "final" / f'cibil_data_with_directors_{safe_def_type}_{date}_for_{state_selection}'

    os.makedirs(raw_output_folder, exist_ok=True)
    os.makedirs(final_output_folder, exist_ok=True)
    
    for state in valid_states:
        try:
            run(date, state, defaulters_type, raw_output_folder, final_output_folder)
        except Exception as e:
            print(f"❌ Error for {state}: {e}")
            logging.error(f"Error for {state}: {e}")
            continue

if __name__ == "__main__":
    print("▶ Running script...")
    logging.info("Running script...")
    data_search()
    merge_data(logging)
    cleaner(logging)
