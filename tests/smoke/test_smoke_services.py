"""
Smoke Testing — chequeo rápido post-deploy de que toda la infraestructura
está en pie antes de correr suites más pesados (integración/regresión).

Se corre primero en el pipeline de CI: si algo acá falla, no tiene sentido
seguir corriendo el resto de los tests.
"""
import socket

import pytest
import requests

from conftest import GRAFANA_URL, GROUND_STATION_URL, MQTT_HOST, MQTT_PORT, PROMETHEUS_URL


def test_mosquitto_acepta_conexiones_tcp():
    with socket.create_connection((MQTT_HOST, MQTT_PORT), timeout=5):
        pass  # si no lanza excepción, el broker está aceptando conexiones


def test_ground_station_expone_metricas():
    resp = requests.get(GROUND_STATION_URL, timeout=5)
    assert resp.status_code == 200


def test_prometheus_esta_healthy():
    resp = requests.get(f"{PROMETHEUS_URL}/-/healthy", timeout=5)
    assert resp.status_code == 200


def test_prometheus_esta_ready():
    resp = requests.get(f"{PROMETHEUS_URL}/-/ready", timeout=5)
    assert resp.status_code == 200


def test_grafana_esta_healthy():
    resp = requests.get(f"{GRAFANA_URL}/api/health", timeout=5)
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("database") == "ok"


def test_prometheus_scrapea_ground_station_correctamente():
    """Confirma que el target 'arsat_telemetry' (ground_station:8000)
    está UP desde el punto de vista de Prometheus, no solo alcanzable
    desde el test runner."""
    resp = requests.get(f"{PROMETHEUS_URL}/api/v1/targets", timeout=5)
    resp.raise_for_status()
    targets = resp.json()["data"]["activeTargets"]

    arsat_targets = [t for t in targets if t["labels"].get("job") == "arsat_telemetry"]
    assert arsat_targets, "No se encontró el target 'arsat_telemetry' en Prometheus"
    assert all(t["health"] == "up" for t in arsat_targets), (
        f"El target de ground_station no está 'up': {arsat_targets}"
    )


def test_reglas_de_alertas_cargadas_en_prometheus():
    """Smoke check de que alerts.yml fue parseado sin errores al arrancar."""
    resp = requests.get(f"{PROMETHEUS_URL}/api/v1/rules", timeout=5)
    resp.raise_for_status()
    groups = resp.json()["data"]["groups"]
    nombres_reglas = {
        rule["name"] for group in groups for rule in group["rules"]
    }
    esperadas = {"CriticalBattery", "HighConsumption", "PayloadOffline"}
    assert esperadas.issubset(nombres_reglas), (
        f"Faltan reglas de alerta. Encontradas: {nombres_reglas}"
    )
