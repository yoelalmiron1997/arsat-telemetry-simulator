"""
Configuración compartida para todos los suites de Pytest.

Todas las URLs/hosts son configurables por variable de entorno para poder
correr los tests tanto en local (contra localhost, con los puertos
publicados por docker-compose) como en un pipeline de CI.
"""
import os
import time

import pytest
import requests

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))

GROUND_STATION_URL = os.getenv("GROUND_STATION_URL", "http://localhost:8000/metrics")
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
GRAFANA_URL = os.getenv("GRAFANA_URL", "http://localhost:3000")

# Nombres de las métricas que el sistema debe exponer siempre.
EXPECTED_METRICS = [
    "arsat_eps_voltage_v",
    "arsat_eps_current_a",
    "arsat_eps_battery_percent",
    "arsat_tcs_solar_temp_c",
    "arsat_tcs_battery_temp_c",
    "arsat_tcs_payload_temp_c",
    "arsat_aocs_pitch_deg",
    "arsat_aocs_roll_deg",
    "arsat_aocs_yaw_deg",
    "arsat_aocs_stars_tracked",
    "arsat_aocs_gps_lat",
    "arsat_aocs_gps_lon",
    "arsat_aocs_gps_alt_km",
    "arsat_payload_status",
    "arsat_payload_downlink_mbps",
    "arsat_payload_uplink_mbps",
]


def parse_prometheus_metric(metrics_text: str, metric_name: str) -> float:
    """Extrae el valor numérico de una métrica del texto plano expuesto
    por prometheus_client (formato de exposición de Prometheus)."""
    for line in metrics_text.splitlines():
        if line.startswith(metric_name + " ") or line.startswith(metric_name + "{"):
            return float(line.split()[-1])
    raise AssertionError(f"Métrica '{metric_name}' no encontrada en la respuesta")


def query_prometheus(promql_query: str) -> dict:
    resp = requests.get(
        f"{PROMETHEUS_URL}/api/v1/query",
        params={"query": promql_query},
        timeout=5,
    )
    resp.raise_for_status()
    return resp.json()


def get_active_alerts() -> list:
    resp = requests.get(f"{PROMETHEUS_URL}/api/v1/alerts", timeout=5)
    resp.raise_for_status()
    return resp.json()["data"]["alerts"]


def wait_until(predicate, timeout_seconds=40, poll_interval=2):
    """Sondea `predicate()` hasta que devuelva un valor 'truthy' o se
    agote el timeout. Devuelve el último valor obtenido."""
    deadline = time.time() + timeout_seconds
    last_value = None
    while time.time() < deadline:
        last_value = predicate()
        if last_value:
            return last_value
        time.sleep(poll_interval)
    return last_value


@pytest.fixture(scope="session")
def metrics_text():
    """Devuelve el contenido crudo del endpoint /metrics de la Ground Station."""
    resp = requests.get(GROUND_STATION_URL, timeout=5)
    resp.raise_for_status()
    return resp.text
