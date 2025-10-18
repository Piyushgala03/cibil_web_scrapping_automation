def extract_directors(page, logging):
    directors = []
    try:
        page.wait_for_selector("table#DirectorInfoTable tr.jqgrow", timeout=60000)
        rows = page.locator("table#DirectorInfoTable tr.jqgrow")
        row_count = rows.count()
        if row_count == 0:
            logging.info("No director rows found in the table.")
            return []
        logging.info(f"Found {row_count} director rows.")
    except Exception as e:
        logging.error(f"Failed to locate director rows: {e}", exc_info=True)
        return []

    for i in range(row_count):
        try:
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
        except Exception as row_err:
            logging.warning(f"Skipped a director row due to error: {row_err}")
    return directors
