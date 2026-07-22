"""
Versión "mock" del Subsistema de Energía (EPS) para el deploy público de
portfolio. En vez de generar valores aleatorios sin fin, recorre en loop
el historial pre-grabado y determinístico de src/mock/history/eps_history.json
(generado por generate_history.py con seed fija).

Publica en el MISMO topic MQTT y con el MISMO formato binario ('!fff') que
power_service.py, así que ground_station.py no necesita ningún cambio: no
distingue entre un dato "real" (aleatorio) y uno "mock" (grabado).

Al llegar al final del historial, vuelve al índice 0 — el "rollback" que
hace que el demo público siempre repita la misma pasada con la misma
anomalía, en vez de mostrar una anomalía distinta cada vez.
"""
import time
import struct
import binascii
import json
import logging
import os

import paho.mqtt.client as mqtt

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [EPS-MOCK] - %(message)s')

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = 1883
MQTT_TOPIC = "arsat/telemetry/eps"

INTERVAL_SECONDS = float(os.getenv("MOCK_INTERVAL_SECONDS", "2"))
HISTORY_PATH = os.getenv(
    "MOCK_HISTORY_PATH",
    os.path.join(os.path.dirname(__file__), "history", "eps_history.json"),
)

with open(HISTORY_PATH, encoding="utf-8") as f:
    HISTORIAL = json.load(f)

client = mqtt.Client()
connected = False
while not connected:
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        connected = True
    except Exception as e:
        logging.warning(f"Esperando al broker MQTT en {MQTT_BROKER}... {e}")
        time.sleep(2)

client.loop_start()


def pack_frame(voltage, current, battery):
    packed_data = struct.pack('!fff', voltage, current, battery)
    return binascii.hexlify(packed_data).decode('utf-8').upper()


logging.info(
    f"Iniciando réplica grabada del Subsistema EPS "
    f"({len(HISTORIAL)} muestras, loop cada {len(HISTORIAL) * INTERVAL_SECONDS:.0f}s)..."
)

indice = 0
try:
    while True:
        muestra = HISTORIAL[indice % len(HISTORIAL)]
        v, c, b = muestra["voltage"], muestra["current"], muestra["battery"]
        hex_frame = pack_frame(v, c, b)

        logging.info(
            f"[{indice % len(HISTORIAL) + 1}/{len(HISTORIAL)}] "
            f"Datos: V={v}V, I={c}A, Bat={b}% -> Trama Hex: 0x{hex_frame}"
        )
        client.publish(MQTT_TOPIC, hex_frame)

        indice += 1
        time.sleep(INTERVAL_SECONDS)
except KeyboardInterrupt:
    logging.info("Apagando réplica del Subsistema EPS...")
    client.loop_stop()
    client.disconnect()
