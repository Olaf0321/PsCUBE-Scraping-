import asyncio
import csv
from googleapiclient.discovery import build
from google.oauth2 import service_account
import os
import sys
import re

def set_stdout(to_file=True):
    if to_file:
        sys.stderr = sys.stdout
    else:
        sys.stderr = sys.__stderr__

def get_checked_rows():
    SHOP_SPREADSHEET_ID = "1fWsztueWu0xxtcZn-FRPzxJaHV1MhbPwcUOi23rV9lY"
    RANGE_NAME = "A1:D"
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    SERVICE_ACCOUNT_FILE = "weighty-vertex-464012-u4-7cd9bab1166b.json"
    # 認証
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    
    # データ取得
    result = sheet.values().get(spreadsheetId=SHOP_SPREADSHEET_ID,
                                range=RANGE_NAME).execute()
    values = result.get('values', [])
    
    if not values:
        print('シートにデータがありません。')
        return []

    headers = values[0]
    checked_rows = []

    # データ行を処理（1行目はヘッダー）
    for row in values[1:]:
        # チェックボックス列が 'TRUE' の行のみ対象
        if len(row) > 0 and row[0].strip().upper() == 'TRUE':
            row_data = {headers[i]: row[i] if i < len(row) else '' for i in range(len(headers))}
            checked_rows.append(row_data)
    
    return checked_rows

def sanitize_filename(filename: str) -> str:
    # Windowsで使えない文字を除去またはアンダースコアに変換
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def extract_sheet_id_from_url(url: str) -> str:
    match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
    if match:
        return match.group(1)
    else:
        return None

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

    filter_rows = [
        row for row in csv_rows
        if [row[0], row[1], row[2]] not in [[r[0], r[1], r[2]] for r in existing_rows]
    ]
    if not filter_rows:
        print("No new rows to append. Exiting.")
        return

    # === COMBINE NEW + OLD ROWS ===
    final_data = [csv_header] + filter_rows + existing_rows

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

    print(f"Data from {CSV_FILE} has been appended to {SHEET_NAME} in spreadsheet {SPREADSHEET_ID}.")                                                                                                                                       

async def slot_send_spreadsheet():
    shop_rows = get_checked_rows()
    if not shop_rows:
        print("チェックされた行がありません。")
        return
    
    # ここで shop_rows を使って処理を行う
    print(f"チェックされた行の数: {len(shop_rows)}")

    for shop in shop_rows:
        shop_url = shop.get("店舗URL")
        print(f"処理中の店舗: {shop_url}")

        # スロット用
        slot_filename = f"result(slot)-{shop_url}.csv"
        slot_filename = sanitize_filename(slot_filename)
        slot_sheet_url = shop.get("スロット用")
        slot_sheet_id = extract_sheet_id_from_url(slot_sheet_url) if slot_sheet_url else None
        print(f"スロット用ファイル名: {slot_filename}, スプレッドシートURL: {slot_sheet_url}, スプレッドシートID: {slot_sheet_id}")

        sheet_name = "全データ集積"

        if os.path.exists(slot_filename) and slot_sheet_id:
            # スロット用のスプレッドシートIDが存在する場合、スプレッドシートにデータを追加
            append_googlespreadsheet(slot_filename, slot_sheet_id, sheet_name)
            print(f"ファイル {slot_filename} のデータをスプレッドシートに追加しました。")
        else:
            print(f"ファイル {slot_filename} またはスプレッドシートIDが存在しません。スキップします。")

def main(to_file=True):
    set_stdout(to_file)
    asyncio.run(slot_send_spreadsheet())

if __name__ == "__main__":
    main(to_file=True)