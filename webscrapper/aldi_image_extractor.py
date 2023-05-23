import asyncio
import os
from playwright.async_api import async_playwright
from urllib.parse import urlparse
from tqdm import tqdm


async def extract_img_links(page, path, sleep_secs):
    categories = path.split("/")
    category = categories[-2]
    category = category.lower().replace(' ', '_').replace(',', '')

    # Get the div element by its class
    div_dropdown = page.locator('div[class="pagination-dropdown"]').nth(0)  # First Element
    li_page_item = div_dropdown.locator('li.page-item').nth(2)  # Third Element
    pages_total = await li_page_item.inner_text()
    pages_total = pages_total[-2]

    # Collect image sources
    for i in range(int(pages_total)):
        # Make the file (to avoid appending text to an existing data).
        # Also provides the headers
        with open(f"{path}{category}_{i}.csv", 'w') as file:
            file.write("category,img_src\n")
            file.close()

        div_selector = 'div[data-qa="search-results"]'
        await page.wait_for_selector(div_selector)
        div_elements = await page.query_selector_all(div_selector)
        for div_element in div_elements:
            img_element = await div_element.query_selector('img')
            img_src = await img_element.get_attribute('src')
            with open(f"{path}{category}_{i}.csv", 'a') as f:
                img_src = img_src.replace("_M.jpg", "_XL.jpg")
                img_src = img_src.replace("_M.png", "_XL.png")
                f.write(f"{category},{img_src}\n")
        next_button = await page.query_selector('a.btn-nav.bg-white[title="Next"]')
        li_page_item = div_dropdown.locator('li.page-item').nth(3)  # Fourth Element
        valid_next_button = await li_page_item.get_attribute("class")
        if "disabled" in valid_next_button:
            break
        await next_button.click()
        await asyncio.sleep(sleep_secs)


async def main(section, url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(url)

        # Wait for the cookie banner to appear
        await page.wait_for_selector('#onetrust-button-group')

        # Click the "Accept All Cookies" button
        await page.click('#onetrust-accept-btn-handler')

        # Wait for the cookie banner to disappear
        await page.wait_for_selector('#onetrust-button-group', state='hidden')

        # Get the text of the h6 element
        text_h = await page.inner_text("#categoryFacets h6")

        text_h = text_h.split("(")[0].strip()

        sleep_secs = 7  # Sleep seconds for asyncio.sleep()

        # Click each button field
        buttons_lvl2 = await page.query_selector_all('div[data-facetfieldname="CategoryLevel2_Facet"] button')

        # Get the text of the div elements
        categories_lvl2 = await page.query_selector_all('div[data-facetfieldname="CategoryLevel2_Facet"]')
        index_lvl2 = 0
        for category in tqdm(categories_lvl2, desc=f"Web-scrapping Aldi {section}..."):
            text_lvl2 = await category.inner_text()
            text_lvl2 = text_lvl2.split("(")[0].strip()

            # Tick on
            # await buttons_lvl2[index_lvl2].click()
            await page.evaluate('(button) => button.click()', buttons_lvl2[index_lvl2])
            await asyncio.sleep(sleep_secs)

            buttons_lvl3 = await page.query_selector_all('div[data-facetfieldname="CategoryLevel3_Facet"] button')

            categories_lvl3 = await page.query_selector_all('div[data-facetfieldname="CategoryLevel3_Facet"]')
            index_lvl3 = 0
            for category_lvl3 in categories_lvl3:
                text_lvl3 = await category_lvl3.inner_text()
                text_lvl3 = text_lvl3.split("(")[0].strip()

                # Tick on
                await page.evaluate('(button) => button.click()', buttons_lvl3[index_lvl3])
                await asyncio.sleep(sleep_secs)

                # Make the dirs
                path = f"../data/aldi/{text_h}/{text_lvl2}/{text_lvl3}/"
                if not os.path.exists(path):
                    os.makedirs(path)

                await extract_img_links(page, path, sleep_secs)

                # Tick off
                await page.evaluate('(button) => button.click()', buttons_lvl3[index_lvl3])
                await asyncio.sleep(sleep_secs)

                index_lvl3 += 1

            if len(categories_lvl3) == 0:
                # Make the dirs, only has lvl2 deep
                path = f"../data/aldi/{text_h}/{text_lvl2}/"
                if not os.path.exists(path):
                    os.makedirs(path)
                await extract_img_links(page, path, sleep_secs)

            # Tick off
            await page.evaluate('(button) => button.click()', buttons_lvl2[index_lvl2])
            await asyncio.sleep(sleep_secs)

            index_lvl2 += 1

        # Close the browser
        await browser.close()

if __name__ == '__main__':
    urls = [
        "https://groceries.aldi.co.uk/en-GB/bakery",
        "https://groceries.aldi.co.uk/en-GB/fresh-food",
        "https://groceries.aldi.co.uk/en-GB/drinks",
        "https://groceries.aldi.co.uk/en-GB/food-cupboard",
        "https://groceries.aldi.co.uk/en-GB/frozen",
        "https://groceries.aldi.co.uk/en-GB/chilled-food",
        "https://groceries.aldi.co.uk/en-GB/baby-toddler",
        "https://groceries.aldi.co.uk/en-GB/health-beauty",
        "https://groceries.aldi.co.uk/en-GB/household",
        "https://groceries.aldi.co.uk/en-GB/pet-care",
    ]

    dataset = {}
    for u in urls:
        parsed_url = urlparse(u)
        last_directory = parsed_url.path.strip("/").split("/")[-1]
        dataset[last_directory] = u

    for section, url in zip(dataset.keys(), dataset.values()):
        asyncio.run(main(section, url))
