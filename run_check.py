"""
Monitor SRE Citas Naturalización — script principal.
Corre cada vez que GitHub Actions lo dispara (vía cron-job.org).
Siempre envía WhatsApp: ALERTA si la página cambió hoy, Sin Cambio si sigue igual.
"""

import os
import sys
import re
from datetime import date, datetime
from dotenv import load_dotenv

from checker import fetch_page, extract_info, load_last_date, save_date
from notifier import send_whatsapp, build_message

load_dotenv()

MESES_ES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}


def parse_fecha(texto):
    """'Última actualización: 28 Mayo 2026' → date(2026, 5, 28)"""
    if not texto:
        return None
    m = re.search(r'(\d{1,2})\s+(\w+)\s+(\d{4})', texto.lower())
    if not m:
        return None
    dia, mes_str, anio = m.groups()
    mes = MESES_ES.get(mes_str)
    if not mes:
        return None
    try:
        return date(int(anio), mes, int(dia))
    except ValueError:
        return None


def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)


def main():
    log("Revisando página SRE...")

    try:
        html = fetch_page()
        info = extract_info(html)
    except Exception as e:
        log(f"Error al descargar página: {e}")
        sys.exit(1)

    last_date_str = load_last_date()
    current_date_str = info["ultima_actualizacion"]
    log(f"Fecha en página : {current_date_str}")
    log(f"Fecha guardada  : {last_date_str or '(ninguna)'}")

    # Determinar si es ALERTA o Sin Cambio
    today = date.today()
    page_date = parse_fecha(current_date_str)
    is_alerta = (
        page_date is not None and page_date >= today  # actualizado hoy o fecha futura
        or current_date_str != last_date_str           # fecha distinta a la guardada
    )

    log(f"Tipo: {'ALERTA' if is_alerta else 'Sin Cambio'}")
    for a in info["anuncios"]:
        log(f"  ▶ {a}")

    phone = os.getenv("CALLMEBOT_PHONE")
    apikey = os.getenv("CALLMEBOT_APIKEY")

    message = build_message(current_date_str, info["anuncios"], alerta=is_alerta)

    try:
        send_whatsapp(phone, apikey, message)
        log("WhatsApp enviado OK")
    except Exception as e:
        log(f"Error al enviar WhatsApp: {e}")
        sys.exit(1)

    save_date(current_date_str)
    log("Snapshot actualizado")


if __name__ == "__main__":
    main()
