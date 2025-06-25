import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Set to True to run headless
        context = await browser.new_context()
        page = await context.new_page()

        url = "https://www.pscube.jp/h/a718736/"
        print(f"Navigating to {url}")
        await page.goto(url, wait_until="load")  # or "networkidle"

        # Wait for the main content area (update selector as needed)
        try:
            await page.wait_for_selector("main", timeout=10000)
            print("Main content loaded.")
        except:
            print("Main content not found within 10 seconds.")

        # Optional: take a screenshot for confirmation
        await page.screenshot(path="screenshot.png")
        print("Screenshot saved.")

        await browser.close()

asyncio.run(run())