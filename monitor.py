"""
Monitor SRE — Bot principal
Corre 3 veces al día durante la última semana del mes.
Uso: python monitor.py
"""

import schedule
import time
import calendar
import os
from datetime import date, datetime
from dotenv import load_dotenv

from checker import fetch_page, extract_info, filter_relevant_announcements, load_last_date, save_date
from notifier import send_whatsapp, build_message

load_dotenv()

PHONE = os.getenv("CALLMEBOT_PHONE")
APIKEY = os.getenv("CALLMEBOT_APIKEY")


def is_last_week_of_month():
    today = date.today()
    last_day = calendar.monthrange(today.year, today.month)[1]
    return today.day >= last_day - 6


def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)


def check():
    if not is_last_week_of_month():
        log("Fuera de última semana del mes — sin revisión")
        return

    log("Revisando página SRE...")

    try:
        html = fetch_page()
        info = extract_info(html)
    except Exception as e:
        log(f"Error al descargar página: {e} — se reintentará en la próxima corrida")
        return

    last_date = load_last_date()
    current_date = info["ultima_actualizacion"]

    if last_date == current_date:
        log(f"Sin cambios — {current_date}")
        return

    # Cambio detectado
    log(f"🚨 CAMBIO DETECTADO: {current_date} (antes: {last_date})")

    anuncios = filter_relevant_announcements(info["anuncios"])
    message = build_message(current_date, anuncios)

    log("Mensaje que se enviará por WhatsApp:")
    print(message)

    if not PHONE or not APIKEY:
        log("⚠ CALLMEBOT_PHONE o CALLMEBOT_APIKEY no configurados en .env — no se envió WhatsApp")
    else:
        try:
            send_whatsapp(PHONE, APIKEY, message)
            log("✓ WhatsApp enviado")
        except Exception as e:
            log(f"✗ Error al enviar WhatsApp: {e}")

    save_date(current_date)
    log("Snapshot actualizado")


# Horarios de revisión (hora local de tu computadora / servidor)
schedule.every().day.at("09:00").do(check)
schedule.every().day.at("14:00").do(check)
schedule.every().day.at("20:00").do(check)

if __name__ == "__main__":
    log("Bot SRE iniciado. Presiona Ctrl+C para detener.")
    log("Horarios: 9:00 AM, 2:00 PM, 8:00 PM")
    check()  # primera corrida inmediata al arrancar
    while True:
        schedule.run_pending()
        time.sleep(60)
