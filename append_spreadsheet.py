import csv
from google.oauth2 import service_account
from googleapiclient.discovery import build

def append_googlespreadsheet(file_name, spreadsheet_id, sheet_name):
    # === CONFIGURATION ===
    CSV_FILE = file_name
    SPREADSHEET_ID = spreadsheet_id
    SHEET_NAME = sheet_name
    SERVICE_ACCOUNT_FILE = 'weighty-vertex-464012-u4-7cd9bab1166b.json'

    # === AUTHENTICATE ===
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)

    # === LOAD CSV ===
    with open(CSV_FILE, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        csv_data = list(reader)

    csv_header = csv_data[0]
    csv_rows = csv_data[1:]  # New data rows

    # === READ EXISTING SHEET DATA ===
    range_all = f"{SHEET_NAME}!A1:Z1000"
    existing = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=range_all
    ).execute().get('values', [])

    if not existing:
        existing_header = csv_header
        existing_rows = []
    else:
        existing_header = existing[0]
        existing_rows = existing[1:]

    # === VALIDATE HEADER MATCH ===
    if existing and existing_header != csv_header:
        raise Exception("Header mismatch between CSV and Google Sheet.")

    # === REMOVE DUPLICATES (from new rows) ===
    existing_set = set(tuple(row) for row in existing_rows)
    unique_new_rows = [row for row in csv_rows if tuple(row) not in existing_set]

    # === COMBINE NEW + OLD ROWS ===
    final_data = [csv_header] + unique_new_rows + existing_rows

    # === CLEAR EXISTING DATA ===
    service.spreadsheets().values().clear(
        spreadsheetId=SPREADSHEET_ID,
        range=range_all,
        body={}
    ).execute()

    # === WRITE MERGED DATA TO SHEET ===
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A1",
        valueInputOption='RAW',
        body={'values': final_data}
    ).execute()

    print(f"✅ 新規の重複なしデータ {len(unique_new_rows)} 行を追加しました（既存データを含めた合計は {len(final_data) - 1} 行）。")                                                                                                                                             
