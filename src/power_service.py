import time
import random
import struct
import binascii
import logging
import paho.mqtt.client as mqtt
import os

# Configuración de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [EPS] - %(message)s')

# Configuración MQTT
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = 1883
MQTT_TOPIC = "arsat/telemetry/eps"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("Conectado al Broker MQTT exitosamente.")
    else:
        logging.error(f"Error al conectar al broker. Código: {rc}")

client = mqtt.Client()
client.on_connect = on_connect

# Conexión con reintentos
connected = False
while not connected:
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        connected = True
    except Exception as e:
        logging.warning(f"Esperando al broker MQTT en {MQTT_BROKER}... {e}")
        time.sleep(2)

client.loop_start()

counter = 0

def get_telemetry():
    global counter
    counter += 1
    
    # Simulamos una anomalía MUY frecuente: cada 15 lecturas (30 seg) dura 5 lecturas (10 seg)
    if counter % 15 < 5:
        voltage = round(random.uniform(20.0, 21.0), 2)  # Caída de tensión
        current = round(random.uniform(10.0, 15.0), 2)  # Consumo excesivo (Ej: Cortocircuito)
        battery = round(random.uniform(10.0, 15.0), 2)  # Batería crítica
    else:
        # Valores normales
        voltage = round(random.uniform(27.5, 28.5), 2)
        current = round(random.uniform(2.0, 5.5), 2)
        battery = round(random.uniform(85.0, 100.0), 2)
        
    return voltage, current, battery

def pack_frame(voltage, current, battery):
    # CCSDS Frame Simulation: Empaquetamos 3 floats en formato binario (12 bytes)
    # '!' indica network (big-endian), 'f' es float (4 bytes)
    packed_data = struct.pack('!fff', voltage, current, battery)
    # Convertimos a Hexadecimal para que sea visible por consola como una trama cruda
    hex_frame = binascii.hexlify(packed_data).decode('utf-8').upper()
    return hex_frame

logging.info("Iniciando simulación del Subsistema de Energía (EPS)...")

try:
    while True:
        v, c, b = get_telemetry()
        hex_frame = pack_frame(v, c, b)
        
        logging.info(f"Datos: V={v}V, I={c}A, Bat={b}% -> Empaquetado a Trama Hex: 0x{hex_frame}")
        
        # Publicamos la trama hexadecimal al broker MQTT
        client.publish(MQTT_TOPIC, hex_frame)
        
        time.sleep(2)
except KeyboardInterrupt:
    logging.info("Apagando Subsistema EPS...")
    client.loop_stop()
    client.disconnect()
