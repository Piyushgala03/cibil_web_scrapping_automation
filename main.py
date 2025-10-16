# main.py

from playwright.sync_api import sync_playwright
import time
import pandas as pd
import ujson as json
import re
import math
import logging
import os
from pathlib import Path
from logger import setup_logger
from wait_for_loader_to_disappear import wait_for_loader_to_disappear
from perform_search import perform_search

def ensure_processed_folder():
    processed_folder = "processed"
    os.makedirs(processed_folder, exist_ok=True)
    return processed_folder

# # ----------------- Basic Logging Setup -----------------
# logging.basicConfig(
#     filename=f"cibil_log_{time.strftime('%Y%m%d_%H%M%S')}.log",
#     level=logging.INFO,
#     format="%(asctime)s - %(levelname)s - %(message)s"
# )

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
        director_data = extract_directors(page)
        return director_data
    except Exception as e:
        print(f"⚠️ Error parsing or fetching directors: {e}")
        logging.error(f"Error parsing or fetching directors: {e}")
        return []

def extract_directors(page):
    page.wait_for_selector("table#DirectorInfoTable tr.jqgrow", timeout=60000)
    directors = []
    rows = page.locator("table#DirectorInfoTable tr.jqgrow")
    row_count = rows.count()
    
    logging.info(f"Found {row_count} director rows.")

    for i in range(row_count):
        row = rows.nth(i)
        director_cells = row.locator('td[aria-describedby="DirectorInfoTable_directorNames"]:not([style*="display:none"])')
        # din_cells = row.locator('td[aria-describedby="DirectorInfoTable_dinNumber"]:not([style*="display:none"]')
        din_cells = row.locator("td[aria-describedby=\"DirectorInfoTable_dinNumber\"]:not([style*=\"display:none\"])")
        pan_cells = row.locator('td[aria-describedby="DirectorInfoTable_dirPans"]:not([style*="display:none"])')

        director_names = [cell.inner_text().strip() for cell in director_cells.all()] if director_cells.count() > 0 else [""]
        din_numbers = [cell.inner_text().strip() for cell in din_cells.all()] if din_cells.count() > 0 else [""]
        pan_numbers = [cell.inner_text().strip() for cell in pan_cells.all()] if pan_cells.count() > 0 else [""]

        max_len = max(len(director_names), len(din_numbers), len(pan_numbers))
        director_names += [""] * (max_len - len(director_names))
        din_numbers += [""] * (max_len - len(din_numbers))
        pan_numbers += [""] * (max_len - len(pan_numbers))

        for dn, din, pan in zip(director_names, din_numbers, pan_numbers):
            directors.append({
                "Directors Reported by Credit Institutions": dn,
                "DIN Number": din,
                "PAN Number": pan
            })
    return directors

# ----------------- Table Extraction -----------------
def extract_table_data(page, date, state, page_no, cibil_link_files, raw_output_folder):
    print("▶ Extracting table data...")
    page.wait_for_selector("table.ui-jqgrid-btable tr.jqgrow", timeout=30000)
    screenshot_path = os.path.join(raw_output_folder, f"{state}_page_{page_no}_no_data.png")

    try:
        rows = page.locator("table.ui-jqgrid-btable tr.jqgrow")
        row_count = rows.count()
        print(f"✅ Found {row_count} rows.")
        logging.info(f"Found {row_count} rows.")
        if row_count == 0:
            raise Exception("No data rows found in table!")

    except Exception as e:
        print(f"⚠️ No data or error extracting table for {state}: {e}")
        logging.error(f"No data or error extracting table for {state}: {e}")

        try:
            page.screenshot(path=screenshot_path, full_page=True)
            print(f"📸 Screenshot saved: {screenshot_path}")
            logging.info(f"Screenshot saved: {screenshot_path}")
        except Exception as ss_err:
            print(f"❌ Failed to capture screenshot: {ss_err}")
            logging.error(f"Failed to capture screenshot: {ss_err}")
        
        # Return empty DataFrame and filename to let main() continue
        empty_df = pd.DataFrame()
        return None, empty_df

    all_rows = []

    for i in range(min(row_count, 2)):
    # for i in range(row_count):
        row = rows.nth(i)
        cells = row.locator("td")
        cell_count = cells.count()
        row_dict = {}

        for j in range(cell_count):
            cell = cells.nth(j)
            if cell.evaluate("el => getComputedStyle(el).display") == "none":
                continue

            header_id = cell.get_attribute("aria-describedby")
            header = header_id.replace("projectTable_", "") if header_id else f"col_{j}"
            text = cell.get_attribute("title") or cell.inner_text().strip()
            row_dict[header] = text

            link_locator = cell.locator("a")
            if link_locator.count() > 0:
                href = link_locator.first.get_attribute("href")
                if href:
                    row_dict[f"{header}_href"] = href

        # row_dict["state"] = state.upper()
        row_dict["date"] = date
        all_rows.append(row_dict)
        print(f"✅ Row {i+1}/{row_count} extracted.")
        logging.info(f"Row {i+1}/{row_count} extracted.")

    df = pd.DataFrame(all_rows)
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_file = f"cibil_data_{date}_{state}_state_page_{page_no}_{timestamp}.xlsx"
    raw_output_file = os.path.join(raw_output_folder, output_file)
    
    df.to_excel(raw_output_file, index=False)
    print(f"💾 Saved {len(df)} rows to {output_file}")
    logging.info(f"Saved {len(df)} rows to {output_file}")
    print("✅ Extraction complete.")
    # cibil_link_files.append(output_file)
    cibil_link_files.append(raw_output_file)
    return output_file, df

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
                output_file, cibil_df = extract_table_data(page, date, state, page_no, cibil_link_files, raw_output_folder)
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
            output_file, cibil_df = extract_table_data(page, date, state, page_no, cibil_link_files, raw_output_folder)
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
            output_with_directors = f"cibil_data_with_directors_{date}_{state}_state_page_{page_no}_{timestamp}.xlsx"
            final_output_with_directors_path = os.path.join(final_output_folder, output_with_directors)
            cibil_df.to_excel(final_output_with_directors_path, index=False)
            print(f"💾 Saved enriched data to {final_output_with_directors_path}")

        browser.close()

# ----------------- Entry Point -----------------
def data_search():
    with open("search_details.json", "r") as f:
        search_details = json.load(f)
    date = search_details.get("date", "31-01-25")
    defaulters_type = search_details.get("defaulters_type", "1 crore")
    state_selection = search_details.get("state_selection", "state")
    print(f'State selection configuration: {state_selection}')

    with open('state_details.json', 'r') as ff:
        state_details = json.load(ff)
    
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
    raw_output_folder = f'cibil_data_{safe_def_type}_{date}_for_{state_selection}'
    final_output_folder = f'cibil_data_with_directors_{safe_def_type}_{date}_for_{state_selection}'

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
