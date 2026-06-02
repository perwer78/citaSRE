"""
TEST LOCAL — Monitor SRE Citas Naturalización
----------------------------------------------
Uso:
    python test_run.py             → scraping + muestra extracción (sin notificar)
    python test_run.py --reset     → borra snapshot y fuerza detección
    python test_run.py --notify    → además envía WhatsApp real (requiere .env)
"""

import sys
import os
from datetime import datetime
from dotenv import load_dotenv

from checker import fetch_page, extract_info, filter_relevant_announcements, load_last_date, save_date, SNAPSHOT_FILE
from notifier import send_whatsapp, build_message

load_dotenv()

LINEA = "=" * 65
NOTIFY = "--notify" in sys.argv


def main():
    if "--reset" in sys.argv:
        if os.path.exists(SNAPSHOT_FILE):
            os.remove(SNAPSHOT_FILE)
            print("[reset] Snapshot borrado — esta corrida forzará detección\n")

    print(LINEA)
    print("  TEST — Monitor SRE Citas Naturalización")
    print(f"  {datetime.now().strftime('%Y-%m-%d  %H:%M:%S')}")
    print(LINEA)

    # 1. Descargar
    print("\n[1] Descargando página de la SRE...")
    try:
        html = fetch_page()
        print("    ✓ Página descargada OK")
    except Exception as e:
        print(f"    ✗ Error: {e}")
        sys.exit(1)

    # 2. Extraer todo
    print("\n[2] Extrayendo información...")
    info = extract_info(html)

    print(f"\n    📅  Fecha de actualización en la página:")
    print(f"        {info['ultima_actualizacion'] or '(no encontrada)'}")

    print(f"\n    📋  Todos los anuncios encontrados ({len(info['anuncios'])}):")
    for i, a in enumerate(info["anuncios"], 1):
        print(f"\n        [{i}] {a}")

    # 3. Filtrar solo los relevantes
    relevantes = filter_relevant_announcements(info["anuncios"])
    print(f"\n    ✂   Anuncios RELEVANTES (se incluirán en la notificación): {len(relevantes)}")
    for i, a in enumerate(relevantes, 1):
        print(f"\n        [{i}] {a}")

    # 4. Comparar con snapshot
    last_date = load_last_date()
    print(f"\n[3] Comparando fechas...")
    print(f"    Guardada : {last_date or '(ninguna — primera ejecución)'}")
    print(f"    Actual   : {info['ultima_actualizacion']}")

    if last_date is None:
        cambio = True
        print("\n    ⚡ PRIMERA EJECUCIÓN — se trata como actualización nueva")
    elif last_date != info["ultima_actualizacion"]:
        cambio = True
        print("\n    🚨 ¡CAMBIO DETECTADO!")
    else:
        cambio = False
        print("\n    ✓  Sin cambios")

    # 5. Notificación
    if cambio:
        message = build_message(info["ultima_actualizacion"], relevantes)

        print("\n" + LINEA)
        print("  MENSAJE QUE SE ENVIARÍA POR WHATSAPP:")
        print(LINEA)
        print()
        print(message)
        print()

        if NOTIFY:
            phone = os.getenv("CALLMEBOT_PHONE")
            apikey = os.getenv("CALLMEBOT_APIKEY")
            if not phone or not apikey:
                print("  ⚠ Faltan CALLMEBOT_PHONE o CALLMEBOT_APIKEY en .env")
            else:
                print("  Enviando WhatsApp real...")
                try:
                    result = send_whatsapp(phone, apikey, message)
                    print(f"  ✓ WhatsApp enviado. Respuesta: {result}")
                except Exception as e:
                    print(f"  ✗ Error: {e}")
        else:
            print("  (Ejecuta con --notify para enviar el WhatsApp real)")

        save_date(info["ultima_actualizacion"])
        print(f"\n  [✓] Snapshot guardado")

    print("\n" + LINEA)
    print("  TEST COMPLETADO")
    print(LINEA + "\n")


if __name__ == "__main__":
    main()
