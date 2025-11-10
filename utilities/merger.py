import os
import pandas as pd
import ujson as json
from pathlib import Path

def merge_data(logger):
    try:
        # Step 1: Current working directory
        # current_path = os.getcwd()
        # current_path = Path.cwd() / "fetched_data" / "final" 
        current_path = Path.cwd() / "fetched_data" / "raw" 
        output_path = Path.cwd() / "fetched_data" / "final"
        output_path.mkdir(parents=True, exist_ok=True)
        current_path.mkdir(parents=True, exist_ok=True)
        logger.info(f'📂 Current folder path: {current_path}\n')

        # Step 2: List all folders containing 'directors'
        folder_list = [f for f in current_path.iterdir() if f.is_dir()]
        logger.info(f'📁 Folders found for processing: {folder_list}\n')

        if not folder_list:
            logger.warning("⚠️ No folders found in 'fetched_data/raw'. Nothing to process.")
            return

        # # Step 3: Load all states from state_details.json
        # with open('configurations/state_details.json') as f:
        #     state_details = json.load(f)
        # all_states = set(state_details.get("all_states", []))
        # logger.info(f'🗂 All states loaded: {all_states}\n')
        # logger.info(f"All states loaded successfully: {len(all_states)} states found.")

        try:
            with open('configurations/state_details.json') as f:
                state_details = json.load(f)
            all_states = set(state_details.get("all_states", []))
            logger.info(f"All states loaded successfully: {len(all_states)} states found.")
        except Exception as e:
            logger.error(f"❌ Failed to load state_details.json: {e}", exc_info=True)
            return

        # Step 4: Initialize dictionary to store files per (state, date)
        state_files = {}

        # Step 5: Process each folder
        for folder in folder_list:
            logger.info(f'--- Opening folder: {folder} ---')
            xlsx_files = [f for f in os.listdir(folder) if f.endswith('.xlsx')]
            logger.info(f'Files found: {xlsx_files}\n')

            for item in xlsx_files:
                parts = item.split("_")
                logger.info(f'Processing file: {item} -> Split parts: {parts}')

                try:
                    state_index = parts.index("state") - 1
                    state_name = parts[state_index]
                    date_index = parts.index("data") + 1
                    file_date = parts[date_index]
                    logger.info(f'Extracted state: {state_name}, date: {file_date}')
                except ValueError as e:
                    state_name = "UNKNOWN"
                    file_date = "UNKNOWN"
                    logger.warning(f"❌ Could not parse state/date from {item}: {e}", exc_info=True)
                    continue

                # Only consider if state is valid
                if state_name in all_states:
                    key = (state_name, file_date)  # ✅ Group by both state and date
                    state_files.setdefault(key, []).append(os.path.join(folder, item))
                    logger.info(f"Added file {item} to key {key}")
                else:
                    logger.warning(f'⚠️ Skipping file: {item}, state {state_name} not found in given states.')

            # logger.info()  # End of folder
            logger.info("--- End of folder processing ---")

        logger.info(f"State-Date wise file mapping created with {len(state_files)} keys.")
        for k, v in state_files.items():
            logger.info(f'  {k}: {v}')
        # logger.info()

        # Step 6: Merge files per (state, date)
        for (state, file_date), file_list in state_files.items():
            merged_date = f'{file_date}' if file_date != "UNKNOWN" else "UNKNOWN_DATE"
            date_folder = os.path.join(output_path, f'{merged_date}_merged')
            os.makedirs(date_folder, exist_ok=True)

            logger.info(f"Starting merge for state={state}, date={file_date}, files={len(file_list)}")

            # Sort files by page number
            try:
                # file_list.sort(key=lambda x: int(x.split("_page_")[1].split("_")[0]))
                file_list.sort(key=lambda x: int(os.path.splitext(x)[0].split("_page_")[1].split("_")[0]))
            except Exception as e:
                logger.warning(f"⚠️ Could not sort by page number for {file_list}: {e}", exc_info=True)
            logger.info(f'Files after sorting by page: {file_list}')

            df_list = []
            for fpath in file_list:
                logger.info(f'📖 Reading file: {fpath}')
                df = pd.read_excel(fpath)
                df['source_date'] = file_date  # Add date column for reference
                logger.info(f'Rows read: {len(df)}')
                df_list.append(df)

            merged_df = pd.concat(df_list, ignore_index=True)
            logger.info(f'🔗 Total rows after merging: {len(merged_df)}')
            if merged_df.empty:
                logger.warning(f"⚠️ No rows found for state={state}, date={file_date}. Skipping save.")
                continue

            # Save merged file in a date subfolder
            output_file = os.path.join(date_folder, f"{merged_date}_{state}_merged.xlsx")
            merged_df.to_excel(output_file, index=False)
            logger.info(f'✅ Merged file saved: {output_file}\n')
    except Exception as e:
        logger.error(f"❌ Unexpected error in merge_data: {e}", exc_info=True)

# if __name__ == '__main__':
#     merge_data()
