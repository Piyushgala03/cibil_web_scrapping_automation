# extract_row_counts.py

import re

def extract_row_counts(page, logging):
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
