import re
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

URL = "https://portales.sre.gob.mx/tramites-dgaj/obtencion-de-cita-para-iniciar-el-tramite-de-naturalizacion"
SNAPSHOT_FILE = "last_snapshot.txt"


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
            print("--- PRIMEROS 2000 CHARS DEL HTML ---")
            print(html[:2000])
            print("--- FIN DEBUG ---")
        browser.close()
    return html


def extract_info(html):
    soup = BeautifulSoup(html, "html.parser")

    # Eliminar ruido: scripts, estilos, navegación
    for tag in soup(["script", "style", "nav", "header", "footer", "meta", "link", "noscript"]):
        tag.decompose()

    # Extraer TODO el texto visible de la página
    full_text = soup.get_text(separator="\n", strip=True)

    # Limpiar líneas en blanco múltiples
    full_text = re.sub(r'\n{3,}', '\n\n', full_text).strip()

    # Detectar la fecha de "Última actualización" (el trigger del bot)
    ultima_actualizacion = None
    for line in full_text.split("\n"):
        if "ltima actualizaci" in line:
            ultima_actualizacion = line.strip()
            break

    return {
        "ultima_actualizacion": ultima_actualizacion,
        "full_text": full_text,
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
