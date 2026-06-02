import requests
from datetime import datetime

CALLMEBOT_URL = "https://api.callmebot.com/whatsapp.php"
PAGE_URL = "https://portales.sre.gob.mx/tramites-dgaj/obtencion-de-cita-para-iniciar-el-tramite-de-naturalizacion"
MAX_CHARS = 1500  # límite seguro para WhatsApp vía CallMeBot


def build_message(ultima_actualizacion, full_text, test_mode=False):
    hora = datetime.now().strftime("%Y-%m-%d %H:%M")
    encabezado = "🧪 TEST: Bot SRE funcionando" if test_mode else "🚨 ALERTA: Citas Naturalización SRE"

    # Incluir el contenido completo pero respetando el límite de caracteres
    contenido = full_text if full_text else "(sin contenido extraído)"
    if len(contenido) > MAX_CHARS:
        contenido = contenido[:MAX_CHARS] + "\n[...texto completo en la página]"

    lines = [
        encabezado,
        f"📅 {ultima_actualizacion or 'Fecha no detectada'}",
        f"🕐 Detectado: {hora}",
        "",
        "📄 CONTENIDO DE LA PÁGINA:",
        contenido,
        "",
        f"🔗 {PAGE_URL}",
    ]
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
