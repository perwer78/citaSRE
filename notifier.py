import requests
from datetime import datetime

CALLMEBOT_URL = "https://api.callmebot.com/whatsapp.php"
PAGE_URL = "https://portales.sre.gob.mx/tramites-dgaj/obtencion-de-cita-para-iniciar-el-tramite-de-naturalizacion"


def build_message(ultima_actualizacion, anuncios, alerta=False):
    hora = datetime.now().strftime("%Y-%m-%d %H:%M")
    encabezado = "🚨 ALERTA: Citas Naturalización SRE" if alerta else "🚨Sin Cambio: Citas Naturalización SRE"

    lines = [
        encabezado,
        f"📅 Página actualizada: {ultima_actualizacion or 'Fecha no detectada'}",
        f"🕐 Detectado: {hora}",
        "",
    ]

    if anuncios:
        for anuncio in anuncios:
            lines.append(f"▶️ {anuncio}")
    else:
        lines.append("(sin anuncios destacados en la página)")

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
