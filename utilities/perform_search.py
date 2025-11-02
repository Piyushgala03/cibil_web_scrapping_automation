# perform_search.py

import math

from utilities.extract_row_counts import extract_row_counts

# ----------------- Perform Search -----------------
def perform_search(page, logger, date, state, defaulters_type, timeout_ms:int = 60000):
    logger.info(f"▶ Performing search for Date:{date}, State:{state}, Defaulters type:{defaulters_type}")
    # if (defaulters_type == '1 crore') or ('crore' in defaulters_type):
    if "crore" in defaulters_type.lower():
        page.wait_for_selector("select#croreAccount", timeout=timeout_ms)
        page.select_option("select#croreAccount", label="Search")

        page.wait_for_selector("select#quarterIdCrore", timeout=timeout_ms)
        page.select_option("select#quarterIdCrore", label=date)

        page.wait_for_selector("img#goForSuitFiledAccounts1CroreId", timeout=timeout_ms)
        page.click("img#goForSuitFiledAccounts1CroreId")

    # elif (defaulters_type == '>25 lacs') or ('25 lacs' in defaulters_type):
    elif "lacs" in defaulters_type.lower():
        page.wait_for_selector("select#lakhAccount", timeout=timeout_ms)
        page.select_option("select#lakhAccount", label="Search")

        page.wait_for_selector("select#quarterIdLakh", timeout=timeout_ms)
        page.select_option("select#quarterIdLakh", label=date)

        page.wait_for_selector("img#goForSuitFiledAccounts25LacsId", timeout=timeout_ms)
        page.click("img#goForSuitFiledAccounts25LacsId")

    page.wait_for_selector("select#stateId", timeout=timeout_ms)
    options = page.locator("select#stateId option",)
    option_texts = []

    count = options.count()
    for i in range(count):
        text = options.nth(i).inner_text().strip()
        if text and text.upper() != "SELECT":
            option_texts.append(text)

    # logger.info(f"✅ Found {len(option_texts)} state options: {option_texts}")
    # logger.info(f"Found {len(option_texts)} state options: {option_texts}")

    if state.lower() != 'all':
        page.select_option("#stateId", label=state.upper())

    page.wait_for_selector("input#searchId", timeout=timeout_ms)
    page.click("input#searchId")
    logger.info("▶ Waiting for search results...")

    # Wait for loader to disappear
    try:
        page.wait_for_selector("div.blockUI.blockMsg.blockPage", state="detached", timeout=timeout_ms)
    except Exception:
        logger.warning("⚠️ Loader did not disappear within timeout period.")

    page.wait_for_timeout(2000)

    page.locator('a[onclick="goToBottom()"]').click()
    page.wait_for_timeout(1000)
    page.locator('a[onclick="goToTop()"]').click()
    page.wait_for_timeout(1000)
    fetched, total = extract_row_counts(page, logger, timeout_ms)
    logger.info(f"▶ Fetched {fetched} out of {total} rows.")
    # pagination_limit = total / 1000
    if total == 0:
        return 0
    else:
        pagination_limit = math.ceil(total / fetched) 
        return pagination_limit
