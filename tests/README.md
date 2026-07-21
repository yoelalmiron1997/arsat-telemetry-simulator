# 🧪 QA Suite — ARSAT Telemetry Simulator

Suite de testing automatizado sobre el simulador, organizado por tipo de
prueba, con un pipeline de CI/CD que lo corre en cada push.

| Carpeta | Tipo | Herramienta | Qué valida |
|---|---|---|---|
| `smoke/` | Smoke Testing | Pytest | Que los 7 servicios (Mosquitto, Prometheus, Grafana, Ground Station) estén sanos y correctamente conectados entre sí antes de correr nada más pesado. |
| `api/` | API Testing | Pytest | Contrato del endpoint `/metrics` de la Ground Station: disponibilidad, formato de exposición Prometheus, rangos físicos válidos de cada métrica. |
| `integration/` | Integration Testing | Robot Framework | Flujo end-to-end determinista: publica una trama binaria conocida en MQTT y verifica que la Ground Station la decodifica y expone exactamente igual en Prometheus. |
| `regression/` | Regression / Fault Injection | Pytest | Observa el ciclo real de anomalías inyectado por `power_service.py` y verifica que las alertas de Prometheus (`alerts.yml`) se disparan y se recuperan correctamente. |

## Cómo correrlo en local

1. Levantar la infraestructura (desde la raíz del repo):
   ```bash
   docker compose up -d --build
   ```

2. Instalar las dependencias de testing:
   ```bash
   cd tests
   pip install -r requirements.txt
   ```

3. Correr cada suite:
   ```bash
   # Smoke (rápido, correr primero)
   pytest smoke -v

   # API
   pytest api -v

   # Integración (Robot Framework)
   cd integration
   robot --outputdir ../../results/robot .
   cd ..

   # Regresión / fault injection (tarda ~1-2 min por los tiempos de espera)
   pytest regression -v
   ```

4. El reporte de Robot Framework queda en `results/robot/report.html` y
   `results/robot/log.html` — abrilos en el navegador para ver el detalle
   paso a paso de cada keyword ejecutado (evidencia trazable de la prueba).

## En CI

El workflow `.github/workflows/ci.yml` corre automáticamente los cuatro
suites en orden (cortando temprano si el smoke test falla) en cada push a
`main` y en cada Pull Request, y publica los reportes (JUnit XML + HTML de
Robot Framework) como artifact descargable desde la pestaña **Actions** de
GitHub.

## Variables de entorno soportadas

Todos los suites resuelven hosts/puertos vía variables de entorno, para
poder correr tanto contra `localhost` (con los puertos publicados por
`docker-compose.yml`) como contra otro entorno:

| Variable | Default |
|---|---|
| `MQTT_HOST` | `localhost` |
| `MQTT_PORT` | `1883` |
| `GROUND_STATION_URL` | `http://localhost:8000/metrics` |
| `PROMETHEUS_URL` | `http://localhost:9090` |
| `GRAFANA_URL` | `http://localhost:3000` |
