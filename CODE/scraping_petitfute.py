import asyncio
import pandas as pd
from urllib.parse import urlparse, parse_qs, unquote
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# ==========================================================
# 0️⃣ Chargement des données source
# ==========================================================
fichier_excel = r"C:\Users\Hanaa\Desktop\PETITFUTE\data\exports\listes_article_octobre.xlsx"
liste_article_octobre = pd.read_excel(fichier_excel)
base_URL = liste_article_octobre[['URL']].dropna().reset_index(drop=True)


# ==========================================================
# 1️⃣ Fonction Playwright pour charger une page dynamiquement
# ==========================================================
async def get_dynamic_html(url):
    """Rend la page (avec JS) et renvoie le HTML final."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/127.0.0.0 Safari/537.36"
            )
        )

        page = await context.new_page()

        # 🔇 Désactiver images, vidéos, pubs pour rapidité
        await page.route("**/*", lambda route: (
            route.continue_()
            if route.request.resource_type in ["document", "script", "xhr", "fetch"]
            else route.abort()
        ))

        try:
            await page.goto(url, timeout=90000, wait_until="domcontentloaded")
            await page.wait_for_timeout(4000)
            html = await page.content()
        except Exception as e:
            print(f"⚠️ Erreur sur {url}: {e}")
            html = ""
        await browser.close()
        return html


# ==========================================================
# 2️⃣ Fonction d’extraction des liens GetYourGuide & Booking
# ==========================================================
def extract_partner_links(html):
    """Extrait tous les liens GetYourGuide et Booking d’un HTML."""
    soup = BeautifulSoup(html, "html.parser")

    links_getyourguide = []
    links_booking = []

    for a in soup.find_all("a", href=True):
        href = a["href"].strip().lower()
        if "getyourguide" in href or "booking.com" in href:
            parsed = urlparse(a["href"])
            qs = parse_qs(parsed.query)
            if "urldeeplink" in qs:
                decoded = unquote(qs["urldeeplink"][0])
            else:
                decoded = a["href"]

            if "getyourguide" in decoded.lower():
                links_getyourguide.append(decoded)
            elif "booking.com" in decoded.lower():
                links_booking.append(decoded)

    return links_getyourguide, links_booking


# ==========================================================
# 3️⃣ Fonction principale de traitement sur un DataFrame
# ==========================================================
async def enrich_dataframe_with_links(df, url_col="URL"):
    """Ajoute deux colonnes au DataFrame : getyourguide_links et booking_links"""
    results_g = []
    results_b = []

    for i, url in enumerate(df[url_col], 1):
        print(f"\n[{i}/{len(df)}] Traitement de {url} ...")
        html = await get_dynamic_html(url)
        gyg, booking = extract_partner_links(html)
        results_g.append(gyg)
        results_b.append(booking)

    df["getyourguide_links"] = results_g
    df["booking_links"] = results_b
    return df


# ==========================================================
# 4️⃣ Exécution principale
# ==========================================================
if __name__ == "__main__":
    print("🚀 Lancement du scraping des liens partenaires Petit Futé...\n")

    df_final = asyncio.run(enrich_dataframe_with_links(base_URL))

    # Sauvegarde du résultat
    sortie = r"C:\Users\Hanaa\Desktop\PETITFUTE\data\outputs\liens_partenaire_octobre.xlsx"
    df_final.to_excel(sortie, index=False)

    print(f"\n✅ Terminé ! Fichier exporté : {sortie}")

