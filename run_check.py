"""
Script de corrida única — usado por GitHub Actions.

Modos:
  python run_check.py           → producción (solo última semana del mes, solo si hay cambio)
  python run_check.py --force   → test (siempre corre, siempre notifica)
"""

import os
import sys
import calendar
from datetime import date, datetime
from dotenv import load_dotenv

from checker import fetch_page, extract_info, load_last_date, save_date
from notifier import send_whatsapp, build_message

load_dotenv()

FORCE = "--force" in sys.argv


def is_last_week_of_month():
    today = date.today()
    last_day = calendar.monthrange(today.year, today.month)[1]
    return today.day >= last_day - 6


def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)


def main():
    if FORCE:
        log("=== MODO TEST — forzando notificación ===")
    else:
        if not is_last_week_of_month():
            log("Fuera de última semana del mes — sin revisión")
            return

    log("Revisando página SRE...")

    try:
        html = fetch_page(debug=FORCE)
        info = extract_info(html)
    except Exception as e:
        log(f"Error al descargar página: {e}")
        sys.exit(1)

    last_date = load_last_date()
    current_date = info["ultima_actualizacion"]
    log(f"Fecha en página : {current_date}")
    log(f"Fecha guardada  : {last_date or '(ninguna)'}")

    if not FORCE and last_date == current_date:
        log("Sin cambios — no se envía notificación")
        return

    message = build_message(current_date, info["full_text"], test_mode=FORCE)
    log("Enviando WhatsApp...")

    phone = os.getenv("CALLMEBOT_PHONE")
    apikey = os.getenv("CALLMEBOT_APIKEY")

    try:
        send_whatsapp(phone, apikey, message)
        log("WhatsApp enviado OK")
    except Exception as e:
        log(f"Error al enviar WhatsApp: {e}")
        sys.exit(1)

    save_date(current_date)
    log("Snapshot actualizado")


if __name__ == "__main__":
    main()
