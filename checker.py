from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

URL = "https://portales.sre.gob.mx/tramites-dgaj/obtencion-de-cita-para-iniciar-el-tramite-de-naturalizacion"
SNAPSHOT_FILE = "last_snapshot.txt"

# Keywords para detectar cualquier anuncio relevante
KEYWORDS = ["CITAS", "NATURALIZ", "DISPONIBLES", "SINNA", "MANTENIMIENTO", "MES DE", "INFORMAMOS"]

# Keywords que identifican anuncios DINÁMICOS (cambian cada mes)
# Los demás son texto fijo de la página que nunca cambia
ANUNCIO_KEYWORDS = [
    "DISPONIBLES EL DÍA",
    "ESTARÁN DISPONIBLES",
    "HABILITADAS EN",
    "MANTENIMIENTO DEL SISTEMA SINNA",
]


def fetch_page():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="es-MX",
        )
        page = context.new_page()
        page.goto(URL, wait_until="networkidle", timeout=60000)
        html = page.content()
        browser.close()
    return html


def extract_info(html):
    soup = BeautifulSoup(html, "html.parser")

    # Buscar "Última actualización"
    ultima_actualizacion = None
    for text_node in soup.find_all(string=True):
        if "ltima actualizaci" in text_node:
            ultima_actualizacion = text_node.strip()
            break

    # Extraer <strong> con contenido relevante
    anuncios = []
    for strong in soup.find_all("strong"):
        texto = strong.get_text(" ", strip=True)
        if any(kw in texto.upper() for kw in KEYWORDS) and len(texto) > 20:
            anuncios.append(texto)

    # Respaldo: párrafos con keywords si no hay <strong>
    if not anuncios:
        for p in soup.find_all("p"):
            texto = p.get_text(" ", strip=True)
            if any(kw in texto.upper() for kw in KEYWORDS) and len(texto) > 30:
                anuncios.append(texto)

    return {
        "ultima_actualizacion": ultima_actualizacion,
        "anuncios": anuncios,
    }


def filter_relevant_announcements(anuncios):
    """Filtra solo los anuncios dinámicos (fecha de liberación y avisos especiales)."""
    return [a for a in anuncios if any(kw in a.upper() for kw in ANUNCIO_KEYWORDS)]


def load_last_date():
    try:
        with open(SNAPSHOT_FILE, "r", encoding="utf-8") as f:
            return f.read().strip() or None
    except FileNotFoundError:
        return None


def save_date(date_str):
    with open(SNAPSHOT_FILE, "w", encoding="utf-8") as f:
        f.write(date_str or "")
