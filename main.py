from playwright.sync_api import sync_playwright
import time
import pandas as pd
import ujson as json
import re
import math
import logging
import os
from pathlib import Path

def ensure_processed_folder():
    processed_folder = "processed"
    os.makedirs(processed_folder, exist_ok=True)
    return processed_folder

# ----------------- Basic Logging Setup -----------------
logging.basicConfig(
    filename=f"cibil_log_{time.strftime('%Y%m%d_%H%M%S')}.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def extract_row_counts(page):
    """
    Extracts the 'fetched' and 'total' row counts from the pagination info div.
    Example text: 'View 1 - 1,000 of 43,116'
    Returns (fetched_count, total_count) as integers.
    """
    # Wait until the pagination info appears
    # page.wait_for_selector('div.ui-paging-info', timeout=10000)
    try:
        page.wait_for_selector('div.ui-paging-info', timeout=10000)
        text = page.locator('div.ui-paging-info').inner_text().strip()
    except Exception:
        print("⚠️ Pagination info not found, returning 0.")
        logging.warning("Pagination info not found, returning 0.")
        return 0, 0
    text = page.locator('div.ui-paging-info').inner_text().strip()
    print(f"📄 Pagination text: {text}")
    logging.info(f"Pagination text: {text}")

    if text.lower() == 'no records':
        logging.info("Found no records for given state")
        return 0, 0
    else:
        # Use regex to extract numbers
        match = re.search(r'View\s*\d+\s*-\s*([\d,]+)\s*of\s*([\d,]+)', text)
        if match:
            fetched = int(match.group(1).replace(',', ''))
            total = int(match.group(2).replace(',', ''))
            print(f"✅ Fetched: {fetched}, Total: {total}")
            return fetched, total
        else:
            print("⚠️ Could not parse pagination info.")
            logging.warning("Could not parse pagination info.")
            return 0, 0


def wait_for_loader_to_disappear(page, timeout=60000):
    """
    Waits for the page loader to disappear.
    
    Args:
        page: Playwright page object.
        timeout: Maximum time to wait for the loader in milliseconds.
    """
    try:
        page.wait_for_selector(
            "div.blockUI.blockMsg.blockPage",
            state="detached",
            timeout=timeout
        )
        print("✅ Loader disappeared.")
        logging.info("Loader disappeared.")
    except Exception:
        print(f"⚠️ Loader did not disappear within {timeout/1000} seconds.")
        logging.warning(f"Loader did not disappear within {timeout/1000} seconds.")


# ----------------- Perform Search -----------------
def perform_search(page, date, state, defaulters_type):
    print("▶ Performing search...")
    logging.info(f"Performing search for date:{date}, state:{state}, Defaulters type:{defaulters_type}")
    if defaulters_type == '1 crore' or 'crore' in defaulters_type:
        page.wait_for_selector("select#croreAccount", timeout=60000)
        page.select_option("select#croreAccount", label="Search")

        page.wait_for_selector("select#quarterIdCrore", timeout=60000)
        page.select_option("select#quarterIdCrore", label=date)

        page.wait_for_selector("img#goForSuitFiledAccounts1CroreId", timeout=60000)
        page.click("img#goForSuitFiledAccounts1CroreId")

    elif defaulters_type == '>25 lacs' or '25 lacs' in defaulters_type:
        page.wait_for_selector("select#lakhAccount", timeout=60000)
        page.select_option("select#lakhAccount", label="Search")

        page.wait_for_selector("select#quarterIdLakh", timeout=60000)
        page.select_option("select#quarterIdLakh", label=date)

        page.wait_for_selector("img#goForSuitFiledAccounts25LacsId", timeout=60000)
        page.click("img#goForSuitFiledAccounts25LacsId")

    page.wait_for_selector("select#stateId", timeout=30000)
    options = page.locator("select#stateId option")
    option_texts = []

    count = options.count()
    for i in range(count):
        text = options.nth(i).inner_text().strip()
        if text and text.upper() != "SELECT":
            option_texts.append(text)

    # print(f"✅ Found {len(option_texts)} state options: {option_texts}")
    # logging.info(f"Found {len(option_texts)} state options: {option_texts}")

    if state.lower() != 'all':
        page.select_option("#stateId", label=state.upper())

    page.wait_for_selector("input#searchId", timeout=60000)
    page.click("input#searchId")
    print("▶ Waiting for search results...")
    logging.info("Waiting for search results...")

    # Wait for loader to disappear
    try:
        page.wait_for_selector("div.blockUI.blockMsg.blockPage", state="detached", timeout=60000)
        print("✅ Loader disappeared after clicking Search.")
        logging.info("Loader disappeared after clicking Search.")
    except Exception:
        print("⚠️ Loader did not disappear within timeout period.")
        logging.warning("Loader did not disappear within timeout period.")

    page.wait_for_timeout(2000)

    page.locator('a[onclick="goToBottom()"]').click()
    page.wait_for_timeout(1000)
    page.locator('a[onclick="goToTop()"]').click()
    page.wait_for_timeout(1000)
    fetched, total = extract_row_counts(page)
    print(f"▶ Fetched {fetched} out of {total} rows.")
    logging.info(f"Fetched {fetched} out of {total} rows.")
    # pagination_limit = total / 1000
    if total == 0:
        return 0
    else:
        pagination_limit = math.ceil(total / fetched) 
        return pagination_limit


# ----------------- Director Extraction -----------------
def extract_directors_from_href(page, href_js, raw_output_folder, final_output_folder):
    try:
        page.evaluate(href_js)
        page.wait_for_load_state("networkidle")
        wait_for_loader_to_disappear(page)
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
        director_cells = row.locator('td[aria-describedby="DirectorInfoTable_directorNames"]')
        din_cells = row.locator('td[aria-describedby="DirectorInfoTable_dinNumber"]')
        pan_cells = row.locator('td[aria-describedby="DirectorInfoTable_dirPans"]')

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

    rows = page.locator("table.ui-jqgrid-btable tr.jqgrow")
    row_count = rows.count()
    print(f"✅ Found {row_count} rows.")
    logging.info(f"Found {row_count} rows.")

    all_rows = []

    for i in range(row_count):
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
    cibil_link_files.append(output_file)
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
        pagination_limit = perform_search(page, date, state, defaulters_type)
        logging.info(f"Pagination limit = {pagination_limit}")

        if pagination_limit > 1:
            print(f"⚠️ More than 1000 rows found ({pagination_limit*1000} total).")

            for i in range(1, int(pagination_limit)+1):
                page_no = i
                output_file, cibil_df = extract_table_data(page, date, state, page_no, cibil_link_files, raw_output_folder)

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
                            wait_for_loader_to_disappear(page)
                            time.sleep(1)
                        except Exception:
                            print("⚠️ Could not navigate back, reloading page...")
                            # Reload the page and re-perform the search to restore state
                            page.reload()
                            page.wait_for_load_state("networkidle")
                            wait_for_loader_to_disappear(page)
                            time.sleep(1)
                            print("🔄 Page reloaded successfully.")

                timestamp = time.strftime("%Y%m%d_%H%M%S")
                output_with_directors = f"cibil_data_with_directors_{date}_{state}_state_page_{i+1}_{timestamp}.xlsx"
                df_for_director_fetch.to_excel(output_with_directors, index=False)
            
            print(f"💾 Saved enriched data to {output_with_directors}")

        else:
            page_no = 1
            output_file, cibil_df = extract_table_data(page, date, state, page_no, cibil_link_files)
            cibil_df["directors_data"] = [[] for _ in range(len(cibil_df))]
            # ----------------- Extract directors row by row -----------------
            for idx, row in cibil_df.iterrows():
                href = row.get("directorName_href", "")
                if isinstance(href, str) and href.startswith("javascript:getDirctorList"):
                    print(f"▶ Extracting directors for row {idx+1}: {row.get('borrowerName','')}")
                    directors = extract_directors_from_href(page, href)
                    cibil_df.at[idx, "directors_data"] = directors

                    try:
                        page.go_back(timeout=60000)
                        page.wait_for_load_state("networkidle")
                        wait_for_loader_to_disappear(page)
                        time.sleep(1)
                    except Exception:
                        print("⚠️ Could not navigate back, reloading page...")
                        # Reload the page and re-perform the search to restore state
                        page.reload()
                        page.wait_for_load_state("networkidle")
                        wait_for_loader_to_disappear(page)
                        time.sleep(1)
                        print("🔄 Page reloaded successfully.")
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_with_directors = f"cibil_data_with_directors_{date}_{state}_state_page_{page_no}_{timestamp}.xlsx"
            final_output_file = os.path.join(final_output_folder, output_file)

            cibil_df.to_excel(final_output_file, index=False)
            print(f"💾 Saved enriched data to {final_output_file}")

        browser.close()

# ----------------- Entry Point -----------------
def data_search():
    with open("search_details.json", "r") as f:
        search_details = json.load(f)
    date = search_details.get("date", "31-01-25")
    defaulters_type = search_details.get("defaulters_type", ["1 crore"])
    state_selection = search_details.get("state_selection", "state")
    print(f'State selection configuration: {state_selection}')

    with open('state_details.json', 'r') as ff:
        state_details = json.load(ff)
    states = state_details.get(state_selection, ["Delhi"])
    print(f'Selected states: {states}')
    
    print(f"▶ Starting batch search for date: {date}")
    logging.info(f"Starting batch search for date: {date}")
    raw_output_folder = os.makedirs(f'cibil_data_{defaulters_type}_{date}_for_{state_selection}', exist_ok=True)
    final_output_folder = os.makedirs(f'cibil_data_{defaulters_type}_{date}_for_{state_selection}', exist_ok=True)
    for state in states:
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
