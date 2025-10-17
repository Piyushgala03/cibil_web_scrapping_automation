# perform_search.py

import math

# from extract_row_counts import extract_row_counts
from utilities.extract_row_counts import extract_row_counts

# ----------------- Perform Search -----------------
def perform_search(page, logging, date, state, defaulters_type):
    print("▶ Performing search...")
    logging.info(f"Performing search for date:{date}, state:{state}, Defaulters type:{defaulters_type}")
    # if (defaulters_type == '1 crore') or ('crore' in defaulters_type):
    if "crore" in defaulters_type.lower():
        page.wait_for_selector("select#croreAccount", timeout=60000)
        page.select_option("select#croreAccount", label="Search")

        page.wait_for_selector("select#quarterIdCrore", timeout=60000)
        page.select_option("select#quarterIdCrore", label=date)

        page.wait_for_selector("img#goForSuitFiledAccounts1CroreId", timeout=60000)
        page.click("img#goForSuitFiledAccounts1CroreId")

    # elif (defaulters_type == '>25 lacs') or ('25 lacs' in defaulters_type):
    elif "lacs" in defaulters_type.lower():
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

    print(f"✅ Found {len(option_texts)} state options: {option_texts}")
    logging.info(f"Found {len(option_texts)} state options: {option_texts}")

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
    fetched, total = extract_row_counts(page, logging)
    print(f"▶ Fetched {fetched} out of {total} rows.")
    logging.info(f"Fetched {fetched} out of {total} rows.")
    # pagination_limit = total / 1000
    if total == 0:
        return 0
    else:
        pagination_limit = math.ceil(total / fetched) 
        return pagination_limit
