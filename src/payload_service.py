import time
import random
import struct
import binascii
import logging
import paho.mqtt.client as mqtt
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [PAYLOAD] - %(message)s')

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = 1883
MQTT_TOPIC = "arsat/telemetry/payload"

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
    status = 1 if random.random() > 0.05 else 0 # 95% activo
    downlink = round(random.uniform(500.0, 1500.0), 2) if status == 1 else 0.0 # Mbps
    uplink = round(random.uniform(200.0, 600.0), 2) if status == 1 else 0.0 # Mbps
    return status, downlink, uplink

def pack_frame(status, downlink, uplink):
    # !iff (status, downlink, uplink)
    packed_data = struct.pack('!iff', status, downlink, uplink)
    return binascii.hexlify(packed_data).decode('utf-8').upper()

logging.info("Iniciando simulación de Carga Útil (Comunicaciones)...")

try:
    while True:
        status, down, up = get_telemetry()
        hex_frame = pack_frame(status, down, up)
        
        estado_str = "ACTIVO" if status == 1 else "FALLA"
        logging.info(f"Estado={estado_str}, Down={down}Mbps, Up={up}Mbps -> Trama Hex: 0x{hex_frame}")
        
        client.publish(MQTT_TOPIC, hex_frame)
        time.sleep(2)
except KeyboardInterrupt:
    client.loop_stop()
    client.disconnect()
