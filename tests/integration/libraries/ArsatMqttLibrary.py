"""
Librería custom de Robot Framework para los tests de integración del
simulador ARSAT.

Expone keywords para:
  - Empaquetar y publicar tramas de telemetría en el mismo formato binario
    que usan los microservicios reales (src/*_service.py), para inyectar
    valores deterministas y verificar que la Ground Station los decodifica
    correctamente end-to-end (satélite -> MQTT -> ground_station -> métrica).
  - Leer el valor actual de una métrica expuesta por la Ground Station.

Cada función pública del módulo queda disponible como keyword en los
archivos .robot (Robot Framework mapea "publish_eps_frame" -> "Publish Eps Frame").
"""
import binascii
import os
import struct
import time

import paho.mqtt.client as mqtt
import requests

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
GROUND_STATION_URL = os.getenv("GROUND_STATION_URL", "http://localhost:8000/metrics")


def _publish(topic: str, hex_frame: str):
    client = mqtt.Client()
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_start()
    client.publish(topic, hex_frame)
    time.sleep(0.5)  # dar tiempo a que el publish salga por la red
    client.loop_stop()
    client.disconnect()


def publish_eps_frame(voltage, current, battery):
    """Publica una trama EPS (voltaje, corriente, batería) igual al
    formato de power_service.py: struct '!fff' -> hex."""
    packed = struct.pack("!fff", float(voltage), float(current), float(battery))
    hex_frame = binascii.hexlify(packed).decode("utf-8")
    _publish("arsat/telemetry/eps", hex_frame)


def publish_tcs_frame(temp_solar, temp_battery, temp_payload):
    """Publica una trama TCS (temperaturas), formato '!fff'."""
    packed = struct.pack("!fff", float(temp_solar), float(temp_battery), float(temp_payload))
    hex_frame = binascii.hexlify(packed).decode("utf-8")
    _publish("arsat/telemetry/tcs", hex_frame)


def publish_aocs_frame(pitch, roll, yaw, stars_tracked, lat, lon, alt_km):
    """Publica una trama AOCS, formato '!fffifff'."""
    packed = struct.pack(
        "!fffifff",
        float(pitch), float(roll), float(yaw),
        int(stars_tracked),
        float(lat), float(lon), float(alt_km),
    )
    hex_frame = binascii.hexlify(packed).decode("utf-8")
    _publish("arsat/telemetry/aocs", hex_frame)


def publish_payload_frame(status, downlink_mbps, uplink_mbps):
    """Publica una trama de Payload, formato '!iff'."""
    packed = struct.pack("!iff", int(status), float(downlink_mbps), float(uplink_mbps))
    hex_frame = binascii.hexlify(packed).decode("utf-8")
    _publish("arsat/telemetry/payload", hex_frame)


def get_metric_value(metric_name):
    """Lee el valor actual de una métrica desde el endpoint /metrics
    de la Ground Station (formato de exposición de Prometheus)."""
    resp = requests.get(GROUND_STATION_URL, timeout=5)
    resp.raise_for_status()
    for line in resp.text.splitlines():
        if line.startswith(metric_name + " ") or line.startswith(metric_name + "{"):
            return float(line.split()[-1])
    raise AssertionError(f"Métrica '{metric_name}' no encontrada en /metrics")
