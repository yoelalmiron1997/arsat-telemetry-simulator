# 🚀 Deploy Público (Portfolio) — ARSAT Telemetry Simulator

## Qué cambia respecto a correrlo en local

**Nada de la arquitectura.** Sigue siendo:

```
Servicios Python (reales o mock) → MQTT (Mosquitto) → Ground Station → Prometheus → Grafana
```

Lo único que cambia para el deploy público son 3 cosas, todas aditivas (no
se tocó ni una línea de `power_service.py`, `thermal_service.py`,
`aocs_service.py`, `payload_service.py` ni `ground_station.py`):

1. **Los 4 generadores de telemetría se reemplazan por su versión "mock"**
   (`src/mock/mock_*.py`), que en vez de generar números aleatorios sin
   fin, reproducen en loop un **historial pre-grabado y determinístico**
   (`src/mock/history/*.json`, generado una sola vez con
   `generate_history.py` y una semilla fija). Publican en el mismo topic
   MQTT y el mismo formato binario que los reales — Ground Station no
   distingue la diferencia.
   - Esto significa que cualquiera que abra el dashboard en cualquier
     momento va a ver **la misma pasada orbital, con la misma anomalía de
     batería en el mismo punto del ciclo** — reproducible, siempre
     mostrable en una entrevista, sin sorpresas.
   - Al llegar al final del historial (180s = 6 ciclos de anomalía), el
     índice vuelve a 0: ese es el "rollback" — el demo se repite solo,
     para siempre, sin necesidad de reiniciar nada a mano.

2. **Mosquitto, Prometheus y Ground Station dejan de publicar puertos al
   host.** Sólo Grafana queda expuesto. Internamente todo se sigue
   comunicando igual (por nombre de servicio en la red de Docker).

3. **La contraseña de Grafana se lee de una variable de entorno**
   (`GF_ADMIN_PASSWORD`) en vez de estar hardcodeada.

## Tu uso local en Docker no cambia en nada

```bash
docker compose up -d --build
```

Este comando sigue haciendo EXACTAMENTE lo mismo que siempre: simuladores
reales con datos aleatorios, y los puertos 1883/9090/8000/3000 publicados
en tu máquina (gracias a `docker-compose.override.yml`, que Compose carga
solo automáticamente cuando no le pasás `-f` a mano). El pipeline de CI
tampoco cambia: sigue corriendo `docker compose up -d --build` tal cual.

## Deploy público, paso a paso

### 1. Conseguir un servidor
Cualquier VPS con Docker (Hetzner, DigitalOcean, Oracle Cloud, o el que
ya veníamos charlando). Solo necesitás abrir el puerto **80** en el
firewall del proveedor (además del 22 para SSH). Nada más.

### 2. Clonar el repo y configurar la password de Grafana
```bash
git clone https://github.com/yoelalmiron1997/arsat-telemetry-simulator.git
cd arsat-telemetry-simulator
cp .env.example .env
nano .env   # completá GF_ADMIN_PASSWORD con algo que no sea "admin"
```

### 3. Levantar el stack en modo público
```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.mock.yml \
  -f docker-compose.prod.yml \
  up -d --build
```

Al pasar `-f` de forma explícita, Compose **no** carga
`docker-compose.override.yml` (eso solo pasa automáticamente cuando no le
pasás ningún `-f`), así que Mosquitto/Prometheus/Ground Station quedan sin
puertos públicos, y Grafana queda mapeado al puerto 80.

### 4. Ver el dashboard
```
http://IP-DE-TU-SERVIDOR
```
Usuario `admin`, la contraseña que pusiste en `.env`.

### 5. Firewall del servidor (por las dudas, además del del proveedor cloud)
```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw enable
```

## Regenerar el historial (opcional)

Si en algún momento querés otro escenario de demo (más anomalías, otra
duración, otra órbita), editá `src/mock/generate_history.py` y volvé a
correrlo:
```bash
cd src/mock
python generate_history.py
```
Esto regenera los 4 archivos `.json` en `src/mock/history/`. Commiteá los
JSON nuevos y volvé a levantar el stack en el servidor.

## Volver a los simuladores reales en el servidor público (si algún día querés)

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```
(sin el `docker-compose.mock.yml`) — mismo servidor, mismos puertos
ocultos, pero con datos 100% aleatorios en vivo en vez del historial
grabado.
