import os
import pandas as pd
import time

def extract_table_data(page, logging, date, state, page_no, cibil_link_files, raw_output_folder):
    print("▶ Extracting table data...")
    try:
        page.wait_for_selector("table.ui-jqgrid-btable tr.jqgrow", timeout=30000)
        rows = page.locator("table.ui-jqgrid-btable tr.jqgrow")
        row_count = rows.count()
        print(f"✅ Found {row_count} rows.")
        logging.info(f"Found {row_count} rows for state: {state}, page: {page_no}.")
        if row_count == 0:
            raise Exception("No data rows found in table!")
    except Exception as e:
        screenshot_path = os.path.join(raw_output_folder, f"{state}_page_{page_no}_no_data.png")
        print(f"⚠️ No data or error extracting table for {state}: {e}")
        logging.error(f"No data or error extracting table for {state}: {e}", exc_info=True)
        try:
            page.screenshot(path=screenshot_path, full_page=True)
            print(f"📸 Screenshot saved: {screenshot_path}")
            logging.info(f"Screenshot saved for state {state}, page {page_no}.")
        except Exception as ss_err:
            print(f"❌ Failed to capture screenshot: {ss_err}")
            logging.error(f"Failed to capture screenshot: {ss_err}", exc_info=True)
        return None, pd.DataFrame()

    all_rows = []
    for i in range(row_count):  # Limit rows for speed
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
            all_rows.append(row_dict)
            print(f"✅ Row {i+1}/{row_count} extracted.")
            logging.info(f"Row {i+1}/{row_count} extracted for {state}.")
        except Exception as row_err:
            logging.warning(f"Skipped a table row due to error: {row_err}")

    df = pd.DataFrame(all_rows)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_file = f"cibil_data_{date}_{state}_state_page_{page_no}_{timestamp}.xlsx"
    raw_output_file = os.path.join(raw_output_folder, output_file)
    df.to_excel(raw_output_file, index=False)

    print(f"💾 Saved {len(df)} rows to {output_file}")
    logging.info(f"Saved {len(df)} rows to {output_file}")
    cibil_link_files.append(raw_output_file)
    return output_file, df