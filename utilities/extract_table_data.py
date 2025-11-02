import os
import pandas as pd

def extract_table_data(page, logging, date, defaulters_type, state, page_no, cibil_link_files, raw_output_folder, timeout_ms:int = 60000):
    logging.info("▶ Extracting table data...")
    try:
        page.wait_for_selector("table.ui-jqgrid-btable tr.jqgrow", timeout=timeout_ms)
        rows = page.locator("table.ui-jqgrid-btable tr.jqgrow")
        row_count = rows.count()
        logging.info(f"Found {row_count} rows for state: {state}, page: {page_no}.")
        if row_count == 0:
            raise Exception("No data rows found in table!")
    except Exception as e:
        screenshot_path = os.path.join(raw_output_folder, f"{defaulters_type}_{state}_page_{page_no}_no_data.png")
        logging.error(f"⚠️ No data or error extracting table for {state}: {e}", exc_info=True)
        try:
            page.screenshot(path=screenshot_path, full_page=True)
            logging.info(f"Screenshot saved for state {state}, page {page_no}.")
        except Exception as ss_err:
            logging.error(f"❌ Failed to capture screenshot: {ss_err}", exc_info=True)
        return None, pd.DataFrame()

    all_rows = []
    for i in range(min(row_count,11)):  # Limit rows for speed
    # for i in range(row_count):
        try:
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

            row_dict["date"] = date
            row_dict["State"] = state
            row_dict['directors_presence'] = 'not_fetched'
            all_rows.append(row_dict)
            logging.info(f"Row {i+1}/{row_count} extracted for {state}.")
        except Exception as row_err:
            logging.warning(f"Skipped a table row due to error: {row_err}")
            raise Exception(f"Scraping failed for current record: {row_err}")

    if len(all_rows) < row_count:
        msg = f"⚠️ Incomplete data: captured {len(all_rows)} of {row_count} rows for {state} (page {page_no})."
        logging.error(msg)
        # raise Exception(msg)
    
    df = pd.DataFrame(all_rows)
    output_file = f"cibil_data_{date}_{defaulters_type}_{state}_state_page_{page_no}.xlsx"
    raw_output_file = os.path.join(raw_output_folder, output_file)
    df.to_excel(raw_output_file, index=False)

    logging.info(f"Saved {len(df)} rows to {output_file}")
    cibil_link_files.append(raw_output_file)
    return df