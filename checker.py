import re
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

URL = "https://portales.sre.gob.mx/tramites-dgaj/obtencion-de-cita-para-iniciar-el-tramite-de-naturalizacion"
SNAPSHOT_FILE = "last_snapshot.txt"

# Colores amarillos que puede usar el gobierno en los estilos CSS
YELLOW_COLORS = ["yellow", "#ffff00", "#ff0", "rgb(255,255,0)", "rgb(255, 255, 0)"]

# Fallback: si no hay amarillo, buscar por keywords conocidos
ANUNCIO_KEYWORDS = [
    "DISPONIBLES EL DÍA", "ESTARÁN DISPONIBLES", "HABILITADAS EN",
    "MANTENIMIENTO DEL SISTEMA", "INFORMAMOS QUE LAS CITAS",
]


def fetch_page(debug=False):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="es-MX",
            geolocation={"longitude": -99.1332, "latitude": 19.4326},
            permissions=["geolocation"],
        )
        page = context.new_page()
        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(3000)
        html = page.content()
        if debug:
            print("--- PRIMEROS 3000 CHARS DEL HTML ---")
            print(html[:3000])
            print("--- FIN DEBUG ---")
        browser.close()
    return html


def _is_yellow(style):
    s = style.lower().replace(" ", "")
    return "background" in s and any(c.replace(" ", "") in s for c in YELLOW_COLORS)


def extract_highlighted(soup):
    """Extrae texto de elementos con fondo amarillo, sin duplicados."""
    seen = set()
    results = []
    for tag in soup.find_all(style=True):
        if _is_yellow(tag.get("style", "")):
            text = tag.get_text(" ", strip=True)
            if text and len(text) > 15 and text not in seen:
                seen.add(text)
                results.append(text)
    return results


def extract_fallback(soup):
    """Si no hay amarillo, busca por keywords en <strong> y párrafos."""
    results = []
    for tag in soup.find_all(["strong", "p"]):
        text = tag.get_text(" ", strip=True)
        if any(kw in text.upper() for kw in ANUNCIO_KEYWORDS) and len(text) > 20:
            results.append(text)
    return results


def extract_info(html):
    soup = BeautifulSoup(html, "html.parser")

    # Detectar fecha de "Última actualización"
    ultima_actualizacion = None
    for text_node in soup.find_all(string=True):
        if "ltima actualizaci" in text_node:
            ultima_actualizacion = text_node.strip()
            break

    # Extraer anuncios amarillos
    anuncios = extract_highlighted(soup)

    # Si no encontró amarillo, usar fallback por keywords
    if not anuncios:
        anuncios = extract_fallback(soup)

    return {
        "ultima_actualizacion": ultima_actualizacion,
        "anuncios": anuncios,
    }


def load_last_date():
    try:
        with open(SNAPSHOT_FILE, "r", encoding="utf-8") as f:
            return f.read().strip() or None
    except FileNotFoundError:
        return None


def save_date(date_str):
    with open(SNAPSHOT_FILE, "w", encoding="utf-8") as f:
        f.write(date_str or "")
