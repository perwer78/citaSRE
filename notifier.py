import requests
import urllib.parse
from datetime import datetime

CALLMEBOT_URL = "https://api.callmebot.com/whatsapp.php"
PAGE_URL = "https://portales.sre.gob.mx/tramites-dgaj/obtencion-de-cita-para-iniciar-el-tramite-de-naturalizacion"


def build_message(ultima_actualizacion, anuncios):
    hora = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "🚨 ALERTA: Citas Naturalización SRE",
        f"📅 Página actualizada: {ultima_actualizacion}",
        f"🕐 Detectado: {hora}",
        "",
    ]
    for anuncio in anuncios:
        lines.append(f"▶ {anuncio}")
    lines += ["", f"🔗 {PAGE_URL}"]
    return "\n".join(lines)


def send_whatsapp(phone, apikey, message):
    params = {
        "phone": phone,
        "text": message,
        "apikey": apikey,
    }
    resp = requests.get(CALLMEBOT_URL, params=params, timeout=30)
    resp.raise_for_status()
    return resp.text
