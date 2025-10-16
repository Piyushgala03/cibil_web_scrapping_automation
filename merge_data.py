import os
import pandas as pd
import ujson as json

def merge_data():
    current_path = os.getcwd()
    print(f'Currect folder path: {current_path}')

    folder_list = [f for f in os.listdir(current_path) if os.path.isdir(f) and 'directors' in str(f)]
    print(folder_list)

    with open('state_details.json') as f:
        state_details = json.load(f)
    all_states = set(state_details.get("all_states", []))
    
    state_files = {}

    for folder in folder_list:
        print(f'opening {folder}')
        for item in [f for f in os.listdir(folder) if f.endswith('.xlsx')]:
            parts = item.split("_")
            try:
                state_index = parts.index("state") - 1
                state_name = parts[state_index]
                date_index = parts.index("directors") + 1
                file_date = parts[date_index]
            except ValueError:
                state_name = "UNKNOWN"
                file_date = "UNKNOWN"
                        # Only consider if state is in all_states
            if state_name in all_states:
                key = (state_name, file_date)  # ✅ Group by both
                state_files.setdefault(key, []).append(os.path.join(folder, item))
            
            print(f'{item} -> {state_name} | {file_date}')
        print()
    # print(f'State wise files:\n{state_files}')
    # Merge files per state
    for (state, file_date), file_info_list in state_files.items():
        # Sort by page number
        file_info_list.sort(key=lambda x: int(x[0].split("_page_")[1].split("_")[0]))
        df_list = [pd.read_excel(f[0]) for f in file_info_list]
        merged_df = pd.concat(df_list, ignore_index=True)

        # Use the first file's date for naming merged file
        # merged_date = file_info_list[0][1]
        output_file = os.path.join(current_path, f"{file_date}_{state}_merged.xlsx")
        merged_df.to_excel(output_file, index=False)
        print(f'✅ Merged file for {state}: {output_file}')

merge_data()