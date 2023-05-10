import asyncio
import os
from playwright.async_api import async_playwright
from urllib.parse import urlparse
from tqdm import tqdm


async def get_image_sources(file, section, url):
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

        # Get the div element by its id
        div_data_pages = page.locator('div[class="pagination-dropdown"]').nth(0)

        # Get the value of the data-pages attribute
        data_pages = await div_data_pages.get_attribute('data-pages')

        # Collect image sources
        for _ in tqdm(range(1, int(data_pages))):
            div_selector = 'div[data-qa="search-results"]'
            await page.wait_for_selector(div_selector)
            div_elements = await page.query_selector_all(div_selector)
            for div_element in div_elements:
                img_element = await div_element.query_selector('img')
                img_src = await img_element.get_attribute('src')
                with open(file, 'a') as f:
                    img_src = img_src.replace("_M.jpg", "_XL.jpg")
                    img_src = img_src.replace("_M.png", "_XL.png")
                    f.write(f"{section},...,{img_src}\n")
            next_button = await page.query_selector('a.btn-nav.bg-white[title="Next"]')
            if not next_button:
                break
            await next_button.click()
            await asyncio.sleep(2)
        await browser.close()

if __name__ == '__main__':
    FILENAME = "aldi_groceries_images.csv"

    if os.path.isfile(FILENAME):
        overwrite = input("The file already exists. Do you want to overwrite it? (y/n) ")

        if overwrite.lower() == 'y':
            # create an empty file
            with open(FILENAME, 'w') as file:
                file.write("section,category,url\n")
            print(f"The file {FILENAME} has been overwritten.")
        else:
            print("Operation cancelled. The file was not overwritten.")
    else:
        # create an empty file
        with open(FILENAME, 'w') as file:
            file.write("section,category,url\n")
        print(f"The file {FILENAME} has been created.")

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
        print(f"{section}, {url}")
        # asyncio.run(get_image_sources(FILENAME, section, url))
