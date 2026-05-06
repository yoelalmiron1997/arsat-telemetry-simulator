import time
import random
import struct
import binascii
import logging
import paho.mqtt.client as mqtt
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [AOCS] - %(message)s')

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = 1883
MQTT_TOPIC = "arsat/telemetry/aocs"

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

# Valores iniciales (Simulando órbita)
BASE_LAT = -34.0
BASE_LON = -71.8
BASE_ALT = 35786.0

def get_telemetry():
    global BASE_LAT, BASE_LON
    
    # Star Tracker: Orientación del satélite
    pitch = round(random.uniform(-0.05, 0.05), 4) # Grados (Ideal 0.0)
    roll = round(random.uniform(-0.05, 0.05), 4)
    yaw = round(random.uniform(-0.05, 0.05), 4)
    stars_tracked = random.randint(4, 12) # Cantidad de estrellas fijadas
    
    # GPS: Posición (Simulamos movimiento orbital rápido para ver un trazo)
    BASE_LON += 1.5  # Se mueve al Este rápidamente
    BASE_LAT += random.uniform(-0.1, 0.1) # Pequeña variación de latitud
    
    if BASE_LON > 180:
        BASE_LON -= 360 # Da la vuelta al mundo
        
    lat = round(BASE_LAT, 4)
    lon = round(BASE_LON, 4)
    alt = round(BASE_ALT + random.uniform(-1.0, 1.0), 2)
    
    return pitch, roll, yaw, stars_tracked, lat, lon, alt

def pack_frame(p, r, y, st, lat, lon, alt):
    # !fff (pitch, roll, yaw) + i (stars_tracked) + fff (lat, lon, alt)
    packed_data = struct.pack('!fffifff', p, r, y, st, lat, lon, alt)
    return binascii.hexlify(packed_data).decode('utf-8').upper()

logging.info("Iniciando simulación del Subsistema AOCS (Star Tracker & GPS)...")

try:
    while True:
        p, r, y, st, lat, lon, alt = get_telemetry()
        hex_frame = pack_frame(p, r, y, st, lat, lon, alt)
        
        log_msg = (f"ST(P:{p}, R:{r}, Y:{y}, Stars:{st}) | "
                   f"GPS(Lat:{lat}, Lon:{lon}, Alt:{alt}km) -> Trama Hex: 0x{hex_frame}")
        logging.info(log_msg)
        
        client.publish(MQTT_TOPIC, hex_frame)
        time.sleep(2)
except KeyboardInterrupt:
    client.loop_stop()
    client.disconnect()
