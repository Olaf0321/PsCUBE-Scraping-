import asyncio
from append_spreadsheet import append_googlespreadsheet
import os

async def pachinko_send_spreadsheet():
    file_name = "result(pachinko).csv"
    spreadsheet_id = "1iFUPPaXyedZODzab1PcREKpRNnrvoKO4noi8b9ZFoVQ"
    sheet_name = "全データ集積"
    # Check if the file exists
    if not os.path.exists(file_name):
        print(f"ファイルが見つかりません: {file_name}")
        return  # Stop execution

    append_googlespreadsheet(file_name, spreadsheet_id, sheet_name)

asyncio.run(pachinko_send_spreadsheet())