"""
API Testing — endpoint de métricas de la Ground Station (:8000/metrics)

Valida el contrato del endpoint que consume Prometheus: disponibilidad,
formato de exposición correcto y presencia/rango válido de cada métrica
de telemetría.
"""
import requests

from conftest import (
    EXPECTED_METRICS,
    GROUND_STATION_URL,
    PROMETHEUS_URL,
    parse_prometheus_metric,
)


def test_metrics_endpoint_responde_200():
    resp = requests.get(GROUND_STATION_URL, timeout=5)
    assert resp.status_code == 200


def test_metrics_endpoint_content_type_prometheus():
    resp = requests.get(GROUND_STATION_URL, timeout=5)
    # prometheus_client expone el formato de texto plano estándar de Prometheus
    assert "text/plain" in resp.headers.get("Content-Type", "")


def test_todas_las_metricas_esperadas_estan_presentes(metrics_text):
    faltantes = [m for m in EXPECTED_METRICS if m not in metrics_text]
    assert not faltantes, f"Métricas no expuestas: {faltantes}"


def test_battery_percent_en_rango_valido(metrics_text):
    valor = parse_prometheus_metric(metrics_text, "arsat_eps_battery_percent")
    assert 0.0 <= valor <= 100.0, f"Batería fuera de rango físico: {valor}%"


def test_voltage_en_rango_plausible(metrics_text):
    # Rango nominal (27.5-28.5V) o de anomalía inyectada (20-21V);
    # nunca debería salir de una banda físicamente razonable.
    valor = parse_prometheus_metric(metrics_text, "arsat_eps_voltage_v")
    assert 15.0 <= valor <= 32.0, f"Voltaje fuera de rango plausible: {valor}V"


def test_payload_status_es_binario(metrics_text):
    valor = parse_prometheus_metric(metrics_text, "arsat_payload_status")
    assert valor in (0.0, 1.0), f"arsat_payload_status debe ser 0 o 1, fue {valor}"


def test_stars_tracked_no_es_negativo(metrics_text):
    valor = parse_prometheus_metric(metrics_text, "arsat_aocs_stars_tracked")
    assert valor >= 0, "La cantidad de estrellas fijadas no puede ser negativa"


def test_prometheus_puede_consultar_la_metrica():
    """Verifica que Prometheus efectivamente scrapeó y puede resolver
    la métrica vía su API de queries (PromQL)."""
    resp = requests.get(
        f"{PROMETHEUS_URL}/api/v1/query",
        params={"query": "arsat_eps_battery_percent"},
        timeout=5,
    )
    resp.raise_for_status()
    body = resp.json()
    assert body["status"] == "success"
    assert len(body["data"]["result"]) > 0, "Prometheus no tiene datos para la métrica"
