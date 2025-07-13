import asyncio
from playwright.async_api import async_playwright
import random
import re
from datetime import datetime, timedelta
import os
import csv
import json

async def human_like_scroll(page, scroll_offset):
    total_scrolled = 0

    while total_scrolled < scroll_offset:
        remaining = scroll_offset - total_scrolled

        # If less than 100px left, scroll that exact amount
        if remaining < 100:
            step = remaining
        else:
            step = random.randint(100, min(500, remaining))

        await page.evaluate(f"window.scrollBy(0, {step})")
        total_scrolled += step

        await asyncio.sleep(random.uniform(0.1, 0.4))

def append_row_to_csv(row_data, filename="result(slot).csv"):
    with open(filename, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(row_data)

async def eachMachineFunc(page, model_name):
    result = []
    await asyncio.sleep(1)

    # await page.wait_for_load_state("load")
    title = await page.title()
    print(f"取得した新しいページタイトル: {title}")
    await human_like_scroll(page, 500)
    # await asyncio.sleep(5)

    extracted_data = [
        "2025-06-28",           # 日付
        title,                 # 機種名（ここではタイトルを機種名の代わりに使用）
        "123",                 # 台番号
        "1000",                # 投入枚数
        "-200",                # 差枚数
        "5",                   # BIG回数
        "2",                   # REG回数
        "2",                   # AT/ART回数
        "500",                 # 累計スタート
        "150",                 # 最終スタート
    ]
    
    # 現在の日付と時刻を取得
    now = datetime.now()

    machine_no = ''

    # div#divDAI の中の <h2> を取得
    h2_element = await page.query_selector('#divDAI h2')

    if h2_element:
        h2_text = await h2_element.inner_text()

        # 正規表現で最後の4桁の数字を抽出
        match = re.search(r'(\d{4})\s*$', h2_text)
        if match:
            machine_no = match.group(1)
        else:
            print("4桁の番号が見つかりませんでした。")
    else:
        print("div#divDAI h2 が見つかりませんでした。")

    # "scroll" クラスの div 内の <tr> を取得
    try:
        scroll_div = await page.wait_for_selector('div.scroll', timeout=3000)
        tr = await scroll_div.query_selector('tr')
    except Exception as e:
        print("⚠️ scroll_div または tr が見つかりませんでした:", e)
        return


    # tr 内のすべての <td> を取得
    tds = await tr.query_selector_all('td')

    # 最初の td をスキップ（index 0）、2番目以降に対して処理
    for i, td in enumerate(tds[1:], start=1):
        if i > 6:
            break  # 最大6日前までに制限
        # td 内のすべての <div class="outer border-bottom"> を取得
        divs = await td.query_selector_all('div.outer.border-bottom')

        # index: 1, 2, 4, 5（0-based index）を抽出
        indices_to_extract = [1, 2, 3, 7, 8]

        values = []
        for j in indices_to_extract:
            if j < len(divs):
                inner_div = await divs[j].query_selector('div.inner.nc-text-align-right')
                if inner_div:
                    text = await inner_div.inner_text()
                    values.append(text.strip())
                else:
                    values.append("")  # inner div not found
            else:
                values.append("")  # index out of range
        
        target_date = now - timedelta(days=i)
        formatted_date = target_date.strftime("%Y/%m/%d")
        extracted_data[0] = formatted_date
        extracted_data[1] = model_name
        extracted_data[2] = machine_no
        extracted_data[3] = extracted_data[4] = ''
        extracted_data[5] = values[0]
        extracted_data[6] = values[1]
        extracted_data[7] = values[2]
        extracted_data[8] = values[3]
        extracted_data[9] = values[4]

        print(extracted_data)

        # データを書き込み
        result.append(extracted_data.copy())
    return result

async def eachModelFunc(page, model_name):
    await asyncio.sleep(1)
    # Step 1: Select the first <td> with the target class
    target_td = await page.query_selector('td.nc-grid-color-fix.nc-text-align-center')
    if not target_td:
        raise Exception("Target <td> not found.")

    # Step 2: Find all <div class="outer border-bottom"> inside that <td>
    divs = await target_td.query_selector_all('div.outer.border-bottom')

    # Step 3: Store the index positions instead of element handles
    num_divs = len(divs)

    response_data = None

    async def handle_response(response):
        nonlocal response_data
        if "nc-m06-001.php" in response.url and response.status == 200:
            try:
                json_data = await response.json()
                print("✅ レスポンス取得成功:", response.url)
                # JSONファイル保存
                with open("slump_graph.json", "w", encoding="utf-8") as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=2)
                response_data = json_data
            except Exception as e:
                print("❌ JSON解析失敗:", e)

    page.on("response", handle_response)

    # Step 4: Loop by index and re-fetch the element each time
    for i in range(1, num_divs):
        await asyncio.sleep(1)
        # Re-query target_td and divs each time after navigation
        target_td = await page.query_selector('td.nc-grid-color-fix.nc-text-align-center')
        if not target_td:
            raise Exception("Target <td> not found after navigation.")

        divs = await target_td.query_selector_all('div.outer.border-bottom')
        if i >= len(divs):
            print(f"インデックス {i} をスキップします。ページ内の div 要素が不足しています。")
            continue

        div = divs[i]

        await human_like_scroll(page, 300)
        # await asyncio.sleep(2)

        try:
            await div.click()
        except Exception as e:
            print(f"インデックス {i} の div をクリックできませんでした：{e}")
            continue

        await page.wait_for_load_state("load")

        # 対象とするグラフタイトル
        target_titles = ["1日前", "2日前", "3日前", "4日前", "5日前", "6日前"]

        # 各日付の右端データを格納するリスト
        right_endpoints = []
        if response_data:
            for title in target_titles:
                try:
                    graph = next(g for g in response_data["Graph"] if g["title"] == title)
                    datas = graph["src"]["datas"]
                    points = [p for p in datas if "out" in p and "value" in p]
                    right = next((p for p in reversed(points) if p["value"] != 0), points[-1])
                    right_endpoints.append({
                        "title": title,
                        "out": right["out"],
                        "value": right["value"]
                    })
                except StopIteration:
                    print(f"⚠ グラフが見つかりませんでした: {title}")
                except Exception as e:
                    print(f"❌ エラー発生（{title}）: {e}")

            # 結果表示
            for data in right_endpoints:
                print(f"📊 {data['title']} の右端: out={data['out']}, value={data['value']}")
        else:
            print("❗ スランプグラフのレスポンスを取得できませんでした。")

        result = await eachMachineFunc(page, model_name)
        print(f"取得した機種データ: {result}")
        if result:
            for index, data in enumerate(right_endpoints):
                # 各日付のデータを追加
                if index < len(result):
                    result[index][3] = data['out']
                    result[index][4] = data['value']
                    append_row_to_csv(result[index])
        else:
            print("❗ 機種データの取得に失敗しました。")

        # Go back to the previous page
        await page.go_back()
        await page.wait_for_load_state("load")

async def run():
    # Define the filename and header
    filename = "result(slot).csv"
    headers = [
        "日付", "機種名", "台番号", "投入枚数", "差枚数", 
        "BIG回数", "REG回数", "AT/ART回数", "累計スタート", "最終スタート"
    ]

    # Check if file exists
    file_exists = os.path.exists(filename)

    # Open the file in write mode (this will truncate it if it exists)
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(headers)  # Always write the header

    print(f'「{filename}」はヘッダーのみで初期化されました。')


    base_url = "https://www.pscube.jp/h/a718736/cgi-bin/nc-v03-001.php?cd_ps=1#4;652"
    initial_page = "https://www.pscube.jp/h/a718736/"
    
    user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--start-maximized",
                "--disable-blink-features=AutomationControlled",
            ]
        )

        context = await browser.new_context(
            user_agent=user_agent,
            viewport={'width': 1024, 'height': 768}
        )

        page = await context.new_page()

        # Hide navigator.webdriver
        await page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        """)

        # Step 1: Go to the initial page
        await page.goto(initial_page)
        await page.evaluate("window.scrollBy(0, 500)")
        await asyncio.sleep(1)

        # Step 2: Click third <td> in first <tr>
        await page.click("table.nc-main-menu > tbody > tr:nth-child(1) > td:nth-child(3) a")

        # Step 3: Wait for list to appear (reCAPTCHA safe)
        await page.wait_for_selector("ul#ulKI > li", timeout=0)

        # 例: 許可された機種名リスト（部分一致などでカスタマイズ可能）
        allowed_titles = ["e真北斗無双5 SFEE"]

        last_len = 0
        scroll_offset = 800
        visited_links = set()

        while True:
            link_title_list = []
            # Scroll down incrementally
            # await page.evaluate(f"window.scrollTo(0, {scroll_offset})")
            await human_like_scroll(page, scroll_offset)
            await page.wait_for_load_state("load")

            # Get all visible <li> elements under #ulKI
            list_items = await page.query_selector_all("ul#ulKI > li")
            print(f"last_len-len(list_items):{last_len}-{len(list_items)}")

            if last_len == len(list_items): break

            for i in range(last_len, len(list_items)):
                li = list_items[i]

                link = await li.query_selector("a")
                if not link:
                    continue

                # 最初の <div> を取得してタイトル抽出
                divs_in_link = await link.query_selector_all("div")
                if not divs_in_link:
                    continue

                first_div = divs_in_link[0]
                title_text = (await first_div.inner_text()).strip()

                href = await link.get_attribute("href")
                if href and href not in visited_links:
                    visited_links.add(href)
                    link_title_list.append((href, title_text))
                    print(f"✅ リンク収集: {href} / タイトル: {title_text}")

            print(f"\n🔎 収集したリンク数: {len(link_title_list)}\n")


            # 🔁 抽出したリンク・タイトルを使ってページ遷移処理
            for href, title_text in link_title_list:
                full_url = base_url.rsplit("/", 1)[0] + "/" + href  # href が相対パスなら補完
                print(f"\n➡️ 遷移: {title_text} - {full_url}")

                await page.goto(full_url)
                await page.wait_for_load_state("load")

                # 実際の処理を実行
                await eachModelFunc(page, title_text)

                # Scroll further for next round
                scroll_offset += 600

            last_len = len(list_items)
            # Go back to the list page
            await page.goto(base_url)
            await page.wait_for_load_state("load")

        print("処理が完了しました。")

        await browser.close()

asyncio.run(run())
