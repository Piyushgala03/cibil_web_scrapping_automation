# extract_row_counts.py

import re

def extract_row_counts(page, logging, timeout_ms:int = 60000):
    """
    Extracts the 'fetched' and 'total' row counts from the pagination info div.
    Example text: 'View 1 - 1,000 of 43,116'
    Returns (fetched_count, total_count) as integers.
    """
    # Wait until the pagination info appears
    # page.wait_for_selector('div.ui-paging-info', timeout=10000)
    try:
        page.wait_for_selector('div.ui-paging-info', timeout=min(timeout_ms, 10000))
        text = page.locator('div.ui-paging-info').inner_text().strip()
    except Exception:
        logging.warning("Pagination not found")
        return 0, 0
    text = page.locator('div.ui-paging-info').inner_text().strip()
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
            logging.info(f"Fetched: {fetched}, Total: {total}")
            return fetched, total
        else:
            logging.warning("Could not parse pagination info.")
            return 0, 0
