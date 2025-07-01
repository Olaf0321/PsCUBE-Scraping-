import asyncio
from slot_eachMachineFunc import eachMachineFunc
from humanLikeScroll import human_like_scroll

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

        await eachMachineFunc(page, model_name)

        # Go back to the previous page
        await page.go_back()
        await page.wait_for_load_state("load")

        # Optional delay
        # await asyncio.sleep(0.5)