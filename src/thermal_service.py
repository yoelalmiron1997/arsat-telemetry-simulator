import time
import random
import struct
import binascii
import logging
import paho.mqtt.client as mqtt
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [TCS] - %(message)s')

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = 1883
MQTT_TOPIC = "arsat/telemetry/tcs"

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

def get_telemetry():
    temp_solar = round(random.uniform(-100.0, 100.0), 2)  # Paneles solares expuestos/ocultos
    temp_battery = round(random.uniform(10.0, 25.0), 2)   # Controlado por calentadores
    temp_payload = round(random.uniform(15.0, 35.0), 2)   # Instrumentos
    return temp_solar, temp_battery, temp_payload

def pack_frame(ts, tb, tp):
    packed_data = struct.pack('!fff', ts, tb, tp)
    return binascii.hexlify(packed_data).decode('utf-8').upper()

logging.info("Iniciando simulación del Subsistema Térmico (TCS)...")

try:
    while True:
        ts, tb, tp = get_telemetry()
        hex_frame = pack_frame(ts, tb, tp)
        
        logging.info(f"Datos: TS={ts}C, TB={tb}C, TP={tp}C -> Trama Hex: 0x{hex_frame}")
        client.publish(MQTT_TOPIC, hex_frame)
        time.sleep(2)
except KeyboardInterrupt:
    client.loop_stop()
    client.disconnect()
