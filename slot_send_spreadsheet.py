import asyncio
from append_spreadsheet import append_googlespreadsheet
import os

async def slot_send_spreadsheet():
    file_name = "result(slot).csv"
    spreadsheet_id = "1ptaunoaTOj4bTicFA6AQMjyZ_Iw0JHCA3nxF2GW1qVE"
    sheet_name = "全データ集積"
    # Check if the file exists
    if not os.path.exists(file_name):
        print(f"ファイルが見つかりません: {file_name}")
        return  # Stop execution
    
    append_googlespreadsheet(file_name, spreadsheet_id, sheet_name)

asyncio.run(slot_send_spreadsheet())