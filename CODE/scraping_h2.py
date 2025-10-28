import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

url = "https://www.booking.com/hotel/fr/hoteldefrancevannes.fr.html?aid=2324560&label=actu_weekend_vannes"

async def get_dynamic_html(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(url, timeout=60000, wait_until="domcontentloaded")
        await page.wait_for_timeout(4000)
        html = await page.content()
        await browser.close()
        return html

def extract_h2_info(html):
    soup = BeautifulSoup(html, "html.parser")
    h2_tags = [h2.get_text(strip=True) for h2 in soup.find_all("h2") if h2.get_text(strip=True)]

    all_h2 = " | ".join(h2_tags) if h2_tags else None

    # Choisir le bon H2
    if h2_tags:
        if h2_tags[0].lower() == "rechercher" and len(h2_tags) > 1:
            target_h2 = h2_tags[1]
        else:
            target_h2 = h2_tags[0]
    else:
        target_h2 = None

    return all_h2, target_h2

async def main():
    html = await get_dynamic_html(url)
    all_h2, second_h2 = extract_h2_info(html)
    print("ALL_H2 =", all_h2)
    print("SECOND_H2 =", second_h2)

asyncio.run(main())
