import time
import struct
import binascii
import logging
import paho.mqtt.client as mqtt
from prometheus_client import start_http_server, Gauge
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [GROUND STATION] - %(message)s')

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = 1883
PROMETHEUS_PORT = 8000

# Definición de Métricas para Prometheus
# EPS
g_voltage = Gauge('arsat_eps_voltage_v', 'Voltaje del bus principal (V)')
g_current = Gauge('arsat_eps_current_a', 'Corriente consumida (A)')
g_battery = Gauge('arsat_eps_battery_percent', 'Nivel de batería (%)')

# TCS
g_temp_solar = Gauge('arsat_tcs_solar_temp_c', 'Temperatura paneles solares (C)')
g_temp_battery = Gauge('arsat_tcs_battery_temp_c', 'Temperatura baterías (C)')
g_temp_payload = Gauge('arsat_tcs_payload_temp_c', 'Temperatura carga útil (C)')

# AOCS
g_pitch = Gauge('arsat_aocs_pitch_deg', 'Pitch (Grados)')
g_roll = Gauge('arsat_aocs_roll_deg', 'Roll (Grados)')
g_yaw = Gauge('arsat_aocs_yaw_deg', 'Yaw (Grados)')
g_stars = Gauge('arsat_aocs_stars_tracked', 'Estrellas fijadas por Star Tracker')
g_lat = Gauge('arsat_aocs_gps_lat', 'Latitud GPS')
g_lon = Gauge('arsat_aocs_gps_lon', 'Longitud GPS')
g_alt = Gauge('arsat_aocs_gps_alt_km', 'Altitud GPS (km)')

# Payload
g_status = Gauge('arsat_payload_status', 'Estado de transpondedores (1=Activo, 0=Falla)')
g_downlink = Gauge('arsat_payload_downlink_mbps', 'Tráfico de bajada (Mbps)')
g_uplink = Gauge('arsat_payload_uplink_mbps', 'Tráfico de subida (Mbps)')


def on_connect(client, userdata, flags, rc):
    logging.info("Conectado al Broker MQTT (Enlace de Radio Simulado). Suscribiéndose a telemetría...")
    client.subscribe("arsat/telemetry/#")

def on_message(client, userdata, msg):
    topic = msg.topic
    hex_frame = msg.payload.decode('utf-8')
    logging.info(f"TRAMA RECIBIDA [{topic}]: 0x{hex_frame} -> Decodificando...")
    
    try:
        # Convertimos de Hex a Binario crudo
        raw_bytes = binascii.unhexlify(hex_frame)
        
        if topic == "arsat/telemetry/eps":
            v, c, b = struct.unpack('!fff', raw_bytes)
            logging.info(f"   [DECODIFICADO EPS] V={round(v,2)}, I={round(c,2)}, Bat={round(b,2)}%")
            g_voltage.set(v)
            g_current.set(c)
            g_battery.set(b)
            
        elif topic == "arsat/telemetry/tcs":
            ts, tb, tp = struct.unpack('!fff', raw_bytes)
            logging.info(f"   [DECODIFICADO TCS] Sol={round(ts,2)}C, Bat={round(tb,2)}C, Pay={round(tp,2)}C")
            g_temp_solar.set(ts)
            g_temp_battery.set(tb)
            g_temp_payload.set(tp)
            
        elif topic == "arsat/telemetry/aocs":
            p, r, y, st, lat, lon, alt = struct.unpack('!fffifff', raw_bytes)
            logging.info(f"   [DECODIFICADO AOCS] ST: P={round(p,4)} R={round(r,4)} Y={round(y,4)} Estrellas={st} | GPS: Lat={round(lat,4)} Lon={round(lon,4)} Alt={round(alt,2)}")
            g_pitch.set(p)
            g_roll.set(r)
            g_yaw.set(y)
            g_stars.set(st)
            g_lat.set(lat)
            g_lon.set(lon)
            g_alt.set(alt)
            
        elif topic == "arsat/telemetry/payload":
            status, down, up = struct.unpack('!iff', raw_bytes)
            logging.info(f"   [DECODIFICADO PAYLOAD] Estado={status}, Down={round(down,2)}Mbps, Up={round(up,2)}Mbps")
            g_status.set(status)
            g_downlink.set(down)
            g_uplink.set(up)
            
    except Exception as e:
        logging.error(f"Error decodificando la trama de {topic}: {e}")

# Iniciar servidor Prometheus
start_http_server(PROMETHEUS_PORT)
logging.info(f"Servidor Prometheus exportando métricas en el puerto {PROMETHEUS_PORT}")

# Configurar MQTT
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

connected = False
while not connected:
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        connected = True
    except Exception:
        logging.warning(f"Esperando al broker MQTT en {MQTT_BROKER}...")
        time.sleep(2)

try:
    client.loop_forever()
except KeyboardInterrupt:
    logging.info("Apagando Estación Terrena...")
    client.disconnect()
