import pandas as pd
import ast  # to safely parse stringified lists/dicts
import time
import os
from pathlib import Path

def expand_directors_data(file_path, output_folder):
    start_time = time.time()
    df = pd.read_excel(file_path, engine="openpyxl")
    df['directors_data'].head()
    df.drop(['borrowerName_href', 'directorName', 'directorName_href', 'source_date'], axis=1, inplace=True)

    # Parse the JSON-like 'directors' column (string → list of dicts)
    df["directors_data"] = df["directors_data"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

    # Expand each director into its own row
    expanded_rows = []
    for _, row in df.iterrows():
        for director in row["directors_data"]:
            new_row = row.copy()
            new_row["Director Name"] = director.get("Directors Reported by Credit Institutions", "")
            new_row["DIN Number"] = director.get("DIN Number", "")
            new_row["PAN Number"] = director.get("PAN Number", "")
            expanded_rows.append(new_row)

    df_expanded = pd.DataFrame(expanded_rows)

    df_expanded.rename(columns={
        'bankName': 'Bank',
        'branchName': 'Branch',
        'quarterDateStr': 'Quarter',
        'borrowerName': 'Borrower Name',
        'regaddr': 'Registered Address',
        'totalAmount': 'OutStanding Amount ( Rs. in Lacs)',
        'directors_data': 'Director Name--DIN no. Detail',
        'Director Name': 'Ind _Director Name',
        'DIN Number': 'DIN NO',
        'PAN Number': 'Director PAN',
    }, inplace=True)

    df_expanded['OutStanding Amount ( Rs. in Lacs)'] = (
    df_expanded['OutStanding Amount ( Rs. in Lacs)']
        .astype(str)                  # ensure everything is string
        .str.replace(',', '', regex=False)  
        .astype(float)                # convert back to float
    )
    df_expanded['Borrower Name'] = df_expanded['Borrower Name'].str.replace(r'\bPVT\b', 'PRIVATE', regex=True)
    df_expanded['Borrower Name'] = df_expanded['Borrower Name'].str.replace(r'\bLTD\b', 'LIMITED', regex=True)

    extra_cols = ['Borrower PAN', 'Final Borrower Name', 'Final_DirectorName','CIN NO','Order Type','Remarks']
    df_expanded[extra_cols] = ''

    print('Column names', df_expanded.columns)

    new_order = ['Bank','Branch','Quarter','Borrower Name','Final Borrower Name','Borrower PAN','Registered Address','Director Name--DIN no. Detail','OutStanding Amount ( Rs. in Lacs)','State','Ind _Director Name','Final_DirectorName','DIN NO','Director PAN','CIN NO','Order Type','Remarks']
    df_expanded = df_expanded[new_order]


    folder, filename = os.path.split(file_path)
    output_file = os.path.join(output_folder, f"final_preprocessed_{filename}")
    df_expanded.to_excel(output_file, index=False)

    print(f"✅ Expanded rows: {len(df_expanded)} -> Saved to: {output_file}")
    print(df_expanded.head())
    end_time = time.time()
    print(f"🕒 Time taken: {round(end_time - start_time, 2)} seconds\n")

def cleaner():
    current_path = Path.cwd() / "fetched_data" / "final" 
    output_folder = current_path.parent / "final_preprocessed"
    os.makedirs(output_folder, exist_ok=True)  # create folder if it doesn't exist
    print(f'📂 Current folder path: {current_path}\n')
    folder_list = [f for f in current_path.iterdir() if f.is_dir() and 'merged' in f.name.lower()]
    print(f'📁 Folders found for processing: {folder_list}\n')
    for folder in folder_list:
        
        print(f'--- Opening folder: {folder} ---')
        xlsx_files = [f for f in os.listdir(folder) if f.endswith('.xlsx')]
        print(f'Files found: {xlsx_files}\n')

        for item in xlsx_files:
            if item.startswith("~$"):
                print(f"Ignoring temporary file: {item}")
                continue
            file_path = os.path.join(folder, item)
            print(f'Processing file: {file_path}')
            expand_directors_data(file_path, output_folder)
