"""
Versión "mock" del Subsistema Térmico (TCS). Ver mock_power.py para la
explicación general del mecanismo de réplica grabada + rollback en loop.
"""
import time
import struct
import binascii
import json
import logging
import os

import paho.mqtt.client as mqtt

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [TCS-MOCK] - %(message)s')

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = 1883
MQTT_TOPIC = "arsat/telemetry/tcs"

INTERVAL_SECONDS = float(os.getenv("MOCK_INTERVAL_SECONDS", "2"))
HISTORY_PATH = os.getenv(
    "MOCK_HISTORY_PATH",
    os.path.join(os.path.dirname(__file__), "history", "tcs_history.json"),
)

with open(HISTORY_PATH, encoding="utf-8") as f:
    HISTORIAL = json.load(f)

client = mqtt.Client()
connected = False
while not connected:
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        connected = True
    except Exception:
        logging.warning(f"Esperando al broker MQTT en {MQTT_BROKER}...")
        time.sleep(2)

client.loop_start()


def pack_frame(ts, tb, tp):
    packed_data = struct.pack('!fff', ts, tb, tp)
    return binascii.hexlify(packed_data).decode('utf-8').upper()


logging.info(
    f"Iniciando réplica grabada del Subsistema TCS "
    f"({len(HISTORIAL)} muestras, loop cada {len(HISTORIAL) * INTERVAL_SECONDS:.0f}s)..."
)

indice = 0
try:
    while True:
        muestra = HISTORIAL[indice % len(HISTORIAL)]
        ts, tb, tp = muestra["temp_solar"], muestra["temp_battery"], muestra["temp_payload"]
        hex_frame = pack_frame(ts, tb, tp)

        logging.info(
            f"[{indice % len(HISTORIAL) + 1}/{len(HISTORIAL)}] "
            f"Datos: TS={ts}C, TB={tb}C, TP={tp}C -> Trama Hex: 0x{hex_frame}"
        )
        client.publish(MQTT_TOPIC, hex_frame)

        indice += 1
        time.sleep(INTERVAL_SECONDS)
except KeyboardInterrupt:
    client.loop_stop()
    client.disconnect()
