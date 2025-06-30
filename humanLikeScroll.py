import random
import asyncio

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