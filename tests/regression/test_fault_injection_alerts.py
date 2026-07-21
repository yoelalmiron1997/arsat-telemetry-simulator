"""
Regression / Fault-Injection Testing.

El subsistema EPS (src/power_service.py) inyecta una anomalía controlada
de forma cíclica: cada 15 lecturas (30s) simula 5 lecturas (10s) de
voltaje bajo + consumo excesivo + batería crítica.

Estos tests observan el sistema en vivo (sin mockear nada) y verifican
que, cuando ese estado degradado efectivamente ocurre, Prometheus lo
detecta y las alertas correspondientes pasan a estado "firing" — y que
luego se recuperan solas cuando el sistema vuelve a valores nominales.

Este es el mismo tipo de validación que respalda el hallazgo de una
incidencia crítica de rendimiento durante la verificación de la OBC del
proyecto SABIA-Mar: no alcanza con que el dato esté disponible, tiene que
disparar la alerta correcta en el momento correcto.
"""
from conftest import get_active_alerts, query_prometheus, wait_until


def _alert_esta_activa(nombre_alerta: str) -> bool:
    alertas = get_active_alerts()
    return any(
        a["labels"].get("alertname") == nombre_alerta and a["state"] == "firing"
        for a in alertas
    )


def _battery_por_debajo_de(umbral: float) -> bool:
    resultado = query_prometheus("arsat_eps_battery_percent")
    data = resultado["data"]["result"]
    if not data:
        return False
    valor = float(data[0]["value"][1])
    return valor < umbral


def _current_por_encima_de(umbral: float) -> bool:
    resultado = query_prometheus("arsat_eps_current_a")
    data = resultado["data"]["result"]
    if not data:
        return False
    valor = float(data[0]["value"][1])
    return valor > umbral


def test_bateria_critica_dispara_alerta_criticalbattery():
    # Nota: este test puede tardar hasta ~45s, ya que espera a que ocurra
    # naturalmente el ciclo de anomalía inyectada por power_service.py.
    # 1) Esperar a que ocurra naturalmente el ciclo de anomalía (batería < 20%)
    en_anomalia = wait_until(lambda: _battery_por_debajo_de(20), timeout_seconds=45)
    assert en_anomalia, (
        "La simulación no generó una lectura de batería < 20% dentro del "
        "tiempo esperado; revisar el ciclo de anomalías en power_service.py"
    )

    # 2) Dar un margen para que Prometheus evalúe la regla (evaluation_interval=5s)
    alerta_activa = wait_until(
        lambda: _alert_esta_activa("CriticalBattery"), timeout_seconds=15
    )
    assert alerta_activa, (
        "La batería cayó por debajo del umbral pero la alerta "
        "'CriticalBattery' no pasó a estado 'firing'"
    )


def test_consumo_excesivo_dispara_alerta_highconsumption():
    en_anomalia = wait_until(lambda: _current_por_encima_de(8), timeout_seconds=45)
    assert en_anomalia, (
        "La simulación no generó un consumo > 8A dentro del tiempo esperado"
    )

    alerta_activa = wait_until(
        lambda: _alert_esta_activa("HighConsumption"), timeout_seconds=15
    )
    assert alerta_activa, (
        "El consumo superó el umbral pero la alerta 'HighConsumption' "
        "no pasó a estado 'firing'"
    )


def test_alertas_de_bateria_se_recuperan_tras_el_ciclo_nominal():
    """Regresión: confirma que las alertas no quedan 'pegadas' en firing
    una vez que el sistema vuelve a valores nominales (evita falsos
    positivos permanentes en el centro de control)."""
    # Esperar a que la batería vuelva a estar por encima del umbral crítico
    recuperado = wait_until(lambda: not _battery_por_debajo_de(20), timeout_seconds=45)
    assert recuperado, "La batería nunca volvió a valores nominales (>20%)"

    # Dar margen a que Prometheus reevalúe la regla y la desactive
    alerta_limpia = wait_until(
        lambda: not _alert_esta_activa("CriticalBattery"), timeout_seconds=15
    )
    assert alerta_limpia, (
        "La alerta 'CriticalBattery' sigue en estado 'firing' pese a que "
        "la batería ya volvió a valores nominales"
    )
