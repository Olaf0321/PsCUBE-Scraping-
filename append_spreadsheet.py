import csv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta

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
        csv_rows = csv_data[1:]

    # === READ EXISTING SHEET DATA ===
    range_all = f"{SHEET_NAME}!A1:Z1000"
    existing = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=range_all
    ).execute().get('values', [])

    # === DECIDE WHAT TO APPEND ===
    if not existing:
        append_values = [csv_header] + csv_rows
    else:
        if existing[0] == csv_header:
            append_values = csv_rows
        else:
            raise Exception("Header mismatch between CSV and Google Sheet.")

    # === APPEND DATA ===
    if append_values:
        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A1",
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body={'values': append_values}
        ).execute()
        print(f"✅ Step 1: Appended {len(append_values)} rows to spreadsheet.")
    else:
        print("ℹ️ No new data to append.")

    # === FETCH DATA AGAIN FOR CLEANUP ===
    all_data = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=range_all
    ).execute().get('values', [])

    if not all_data or len(all_data) < 2:
        print("ℹ️ Not enough data to clean.")
        exit()

    header = all_data[0]
    rows = all_data[1:]

    # === REMOVE DUPLICATES (normalized row) ===
    unique_set = set()
    unique_rows = []

    for row in rows:
        row_tuple = tuple(row)
        if row_tuple not in unique_set:
            unique_set.add(row_tuple)
            unique_rows.append(row)  # Keep only the first occurrence

    # === SORT BY '日付' COLUMN ===
    if '日付' in header:
        def parse_date(value):
            value = value.strip().lstrip("'")
            try:
                return datetime.strptime(value, "%Y/%m/%d")
            except ValueError:
                try:
                    return datetime(1899, 12, 30) + timedelta(days=int(float(value)))
                except Exception as e:
                    print(f"⚠️ Skipping invalid date: {value} ({e})")
                    return datetime.max  # Puts invalid dates at the end

        unique_rows.sort(key=lambda row: parse_date(row[0]))
    else:
        print("⚠️ '日付' column not found. Skipping sort.")

    # === OVERWRITE CLEANED DATA BACK TO SHEET ===
    final_data = [header] + unique_rows

    # Clear existing contents
    clear_values_request = {}
    service.spreadsheets().values().clear(
        spreadsheetId=SPREADSHEET_ID,
        range=SHEET_NAME,
        body=clear_values_request
    ).execute()

    # Write new data
    final_data = [header] + unique_rows
    body = {
        'values': final_data
    }
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=SHEET_NAME,
        valueInputOption='RAW',
        body=body
    ).execute()

    print(f"✅ Step 2: Cleaned {len(rows)} rows → {len(unique_rows)} unique rows sorted by '日付'.")                                                                                                                                                    
