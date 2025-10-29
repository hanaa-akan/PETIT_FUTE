import asyncio
import pandas as pd
import ast
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# ==========================================================
# 0️⃣ Chargement du fichier
# ==========================================================
fichier = r"C:\Users\Hanaa\Desktop\PETITFUTE\data\outputs\liens_partenaire_octobre.xlsx"
df = pd.read_excel(fichier)

# Garder seulement URL et booking_links
df = df[["URL", "booking_links"]].dropna()

# Transformer les listes stockées comme texte en vraies listes
df["booking_links"] = df["booking_links"].apply(
    lambda x: ast.literal_eval(x) if isinstance(x, str) else x
)

# Exploser → une ligne par URL / booking_link
df_exploded = df.explode("booking_links").reset_index(drop=True)

# Nettoyage : supprimer les NaN et garder que les vrais liens
df_exploded = df_exploded.dropna(subset=["booking_links"])
df_exploded = df_exploded[
    df_exploded["booking_links"].astype(str).str.startswith("http")
].reset_index(drop=True)

# ==========================================================
# 1️⃣ Fonction Playwright : récupérer le HTML dynamique
# ==========================================================
async def get_dynamic_html(url):
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
        try:
            await page.goto(url, timeout=60000, wait_until="domcontentloaded")
            await page.wait_for_timeout(4000)
            html = await page.content()
        except Exception as e:
            print(f"⚠️ Erreur sur {url}: {e}")
            html = ""
        await browser.close()
        return html

# ==========================================================
# 2️⃣ Fonction extraction H2
# ==========================================================
def extract_booking_title(html):
    soup = BeautifulSoup(html, "html.parser")

    h2_tags = [h.get_text(strip=True) for h in soup.find_all("h2") if h.get_text(strip=True)]
    if not h2_tags:
        return None

    # mots-clés à ignorer si c’est le premier h2
    exclude_first = ["rechercher", "search", "find", "chercher"]

    first = h2_tags[0].lower()

    # si le 1er est une variante de "rechercher" → on prend le suivant
    if any(word in first for word in exclude_first) and len(h2_tags) > 1:
        return h2_tags[1]
    else:
        return h2_tags[0]

# ==========================================================
# 3️⃣ Boucle principale : enrichir le DF avec le H2
# ==========================================================
async def enrich_with_h2(df, url_col="booking_links"):
    h2_list = []
    for i, url in enumerate(df[url_col], 1):
        print(f"[{i}/{len(df)}] {url}")
        if not isinstance(url, str) or not url.startswith("http"):
            h2_list.append(None)
            continue
        html = await get_dynamic_html(url)
        h2_text = extract_booking_title(html)
        h2_list.append(h2_text)
        print(f"  → {h2_text}")
    df["balise_h2"] = h2_list
    return df

# ==========================================================
# 4️⃣ Exécution globale
# ==========================================================
if __name__ == "__main__":
    print("🚀 Extraction des balises <h2> Booking...\n")
    df_final = asyncio.run(enrich_with_h2(df_exploded))

    sortie = r"C:\Users\Hanaa\Desktop\PETITFUTE\data\outputs\booking_h2_exploded.xlsx"
    df_final.to_excel(sortie, index=False)

    print(f"\n✅ Terminé ! Fichier exporté : {sortie}")
