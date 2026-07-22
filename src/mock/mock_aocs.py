"""
Versión "mock" del Subsistema AOCS (Star Tracker & GPS). Ver mock_power.py
para la explicación general del mecanismo de réplica grabada + rollback.
"""
import time
import struct
import binascii
import json
import logging
import os

import paho.mqtt.client as mqtt

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [AOCS-MOCK] - %(message)s')

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = 1883
MQTT_TOPIC = "arsat/telemetry/aocs"

INTERVAL_SECONDS = float(os.getenv("MOCK_INTERVAL_SECONDS", "2"))
HISTORY_PATH = os.getenv(
    "MOCK_HISTORY_PATH",
    os.path.join(os.path.dirname(__file__), "history", "aocs_history.json"),
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


def pack_frame(p, r, y, st, lat, lon, alt):
    packed_data = struct.pack('!fffifff', p, r, y, st, lat, lon, alt)
    return binascii.hexlify(packed_data).decode('utf-8').upper()


logging.info(
    f"Iniciando réplica grabada del Subsistema AOCS "
    f"({len(HISTORIAL)} muestras, loop cada {len(HISTORIAL) * INTERVAL_SECONDS:.0f}s)..."
)

indice = 0
try:
    while True:
        m = HISTORIAL[indice % len(HISTORIAL)]
        p, r, y = m["pitch"], m["roll"], m["yaw"]
        st, lat, lon, alt = m["stars_tracked"], m["lat"], m["lon"], m["alt"]
        hex_frame = pack_frame(p, r, y, st, lat, lon, alt)

        logging.info(
            f"[{indice % len(HISTORIAL) + 1}/{len(HISTORIAL)}] "
            f"ST(P:{p}, R:{r}, Y:{y}, Stars:{st}) | "
            f"GPS(Lat:{lat}, Lon:{lon}, Alt:{alt}km) -> Trama Hex: 0x{hex_frame}"
        )
        client.publish(MQTT_TOPIC, hex_frame)

        indice += 1
        time.sleep(INTERVAL_SECONDS)
except KeyboardInterrupt:
    client.loop_stop()
    client.disconnect()
