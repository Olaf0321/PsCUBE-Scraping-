import asyncio
from playwright.async_api import async_playwright
from slot_eachModelFunc import eachModelFunc
from humanLikeScroll import human_like_scroll
import os
import csv

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

    print(f'"{filename}" is now initialized with header only.')

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
                scroll_offset += 300

            last_len = len(list_items)
            # Go back to the list page
            await page.goto(base_url)
            await page.wait_for_load_state("load")

        print(f"The end")

        await browser.close()

asyncio.run(run())
