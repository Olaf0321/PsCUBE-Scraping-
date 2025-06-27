import asyncio
import random
from playwright.async_api import async_playwright

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

# Placeholder: Define your processing logic here
async def function1(page, link):
    print(f"Running function1 on detail page...{link}")
    human_like_scroll(page, 500)
    # await asyncio.sleep(12)  # Simulate processing time

async def run():
    base_url = "https://www.pscube.jp/h/a718736/cgi-bin/nc-v03-001.php?cd_ps=1#4;652"
    initial_page = "https://www.pscube.jp/h/a718736/"
    scroll_offset = 800
    visited_links = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # Step 1: Go to the initial page
        await page.goto(initial_page)
        await page.evaluate("window.scrollBy(0, 500)")
        await asyncio.sleep(1)

        # Step 2: Click second <td> in first <tr>
        await page.click("table.nc-main-menu > tbody > tr:nth-child(1) > td:nth-child(2) a")

        # Step 3: Wait for list to appear (reCAPTCHA safe)
        await page.wait_for_selector("ul#ulKI > li", timeout=0)

        while True:
            # Scroll down incrementally
            # await page.evaluate(f"window.scrollTo(0, {scroll_offset})")
            await human_like_scroll(page, scroll_offset)
            await asyncio.sleep(10)

            # Get all visible <li> elements under #ulKI
            list_items = await page.query_selector_all("ul#ulKI > li")
            new_link_found = False

            for li in list_items:
                link = await li.query_selector("a")
                if link:
                    href = await link.get_attribute("href")
                    if href and href not in visited_links:
                        visited_links.add(href)

                        # Click the <a> tag to go to detail page
                        await link.click()
                        await page.wait_for_load_state("load")

                        # Optional: Wait until content loads (in case of captcha)
                        await asyncio.sleep(1)

                        # Execute your function
                        await function1(page, link)

                        await asyncio.sleep(12)

                        # Go back to the list page
                        await page.goto(base_url)

                        # Wait until list reappears (handles reCAPTCHA if needed)
                        await page.wait_for_selector("ul#ulKI > li", timeout=0)

                        # Scroll further for next round
                        scroll_offset += 100
                        new_link_found = True
                        break  # Exit current loop and re-evaluate <li>s

            if not new_link_found:
                print("No new links found. Ending loop.")
                break

        await browser.close()

asyncio.run(run())
