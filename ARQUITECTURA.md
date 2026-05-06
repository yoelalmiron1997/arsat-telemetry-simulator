# Arquitectura Técnica - Simulador ARSAT

Este documento describe la estructura técnica, componentes y flujo de datos del simulador del satélite ARSAT, diseñado mediante una arquitectura orientada a microservicios e instrumentado con un stack moderno de observabilidad.

---

## 1. Visión General del Sistema

El proyecto simula los subsistemas críticos de un satélite geoestacionario de telecomunicaciones (como el ARSAT-1 o ARSAT-2). Los componentes internos del "satélite" generan telemetría en tiempo real, la codifican en tramas binarias (representadas en formato hexadecimal para simular telemetría real por radiofrecuencia) y la transmiten a una "Estación Terrena".

La estación terrena decodifica estas tramas y expone las métricas para su consumo por un stack de monitoreo, permitiendo la visualización en vivo de la salud del satélite y la detección de anomalías.

---

## 2. Diagrama de Arquitectura

```mermaid
flowchart TD
    subgraph Satélite ARSAT (Microservicios)
        EPS[EPS - Energía\npower_service.py]
        TCS[TCS - Control Térmico\nthermal_service.py]
        AOCS[AOCS - Actitud y Órbita\naocs_service.py]
        PAY[PAYLOAD - Carga Útil\npayload_service.py]
    end

    MQTT{{Broker MQTT\n(Mosquitto)}}

    subgraph Tierra
        GS[Estación Terrena\nground_station.py]
        PROM[(Prometheus\nBase de Datos y Alertas)]
        GRAF[Grafana\nDashboard y Mapas]
    end

    %% Flujos de datos
    EPS -- "Telemetría (Hex)" --> MQTT
    TCS -- "Telemetría (Hex)" --> MQTT
    AOCS -- "Telemetría (Hex)" --> MQTT
    PAY -- "Telemetría (Hex)" --> MQTT

    MQTT -- "Suscripción" --> GS
    GS -- "Expone Métricas\n(Puerto 8000)" --> PROM
    PROM -- "Consulta de Datos" --> GRAF
```

---

## 3. Subsistemas del Satélite (Microservicios Python)

Cada subsistema es un contenedor Docker independiente que ejecuta un script en Python.

*   **EPS (Electrical Power Subsystem - `power_service.py`):**
    *   **Función:** Simula la generación y consumo de energía.
    *   **Variables:** Nivel de batería (%), Voltaje del Bus (V), Corriente (A).
    *   **Comportamiento Especial:** Cuenta con un inyector de anomalías que cada 40 segundos provoca una caída de batería y un pico de consumo para disparar alarmas.
*   **TCS (Thermal Control System - `thermal_service.py`):**
    *   **Función:** Simula la temperatura de las distintas partes críticas expuestas al sol y a la sombra.
    *   **Variables:** Temperatura de paneles solares, baterías y carga útil (°C).
*   **AOCS (Attitude and Orbit Control System - `aocs_service.py`):**
    *   **Función:** Simula la orientación del satélite y su posicionamiento GPS global.
    *   **Variables:** Pitch, Roll, Yaw (grados), Estrellas fijadas (Star Tracker), Latitud, Longitud, Altitud (~35,786 km).
*   **Payload (`payload_service.py`):**
    *   **Función:** Simula la carga útil de telecomunicaciones (Transpondedores Ku/Ka).
    *   **Variables:** Tráfico de subida y bajada (Mbps), Estado operativo (1=Online, 0=Offline).

---

## 4. Protocolo de Comunicación (Enlace Espacio-Tierra)

La comunicación entre el satélite y la Tierra está abstraída mediante un **Broker MQTT (Eclipse Mosquitto)** corriendo en el puerto `1883`.

*   **Codificación:** Los microservicios no envían texto plano. Usan la librería `struct` de Python para empaquetar los floats y enteros en binario crudo (simulando tramas de espacio profundo estilo CCSDS), y luego los envían codificados en formato Hexadecimal.
*   **Tópicos MQTT:** `arsat/telemetry/eps`, `arsat/telemetry/tcs`, `arsat/telemetry/aocs`, `arsat/telemetry/payload`.

---

## 5. Estación Terrena y Observabilidad

### Estación Terrena (`ground_station.py`)
Actúa como puente. Se suscribe a todos los tópicos del broker MQTT, recibe las tramas hexadecimales, las desempaqueta (`struct.unpack`) de vuelta a valores legibles y los asigna a objetos *Gauge* de la librería `prometheus_client`. Expone estos datos en un servidor HTTP en el puerto `8000`.

### Prometheus (`/prometheus`)
*   **Scraping:** Configurado en `prometheus.yml` para leer los datos de la estación terrena cada 5 segundos.
*   **Motor de Reglas:** Contiene un archivo `alerts.yml` que evalúa constantemente las métricas. Dispara alarmas automáticas si:
    *   Batería < 20%
    *   Temperatura de paneles > 80°C
    *   Consumo de corriente > 8A
    *   Carga útil en estado de falla (0).

### Grafana (`/grafana`)
*   **Aprovisionamiento Automático:** Configurado sin intervención manual usando la carpeta `provisioning/`. Conecta Prometheus automáticamente y pre-carga el dashboard de ARSAT.
*   **Visualización:** Incluye un Geomap para plotear la Latitud y Longitud en un mapa de la Tierra, medidores de estados (Gauges) con umbrales semaforizados, gráficos de área para temperaturas, y una Tabla Dinámica consultando a Prometheus para listar alertas activas en tiempo real.

---

## 6. Despliegue e Infraestructura

El proyecto entero está orquestado mediante **Docker Compose** (`docker-compose.yml`), asegurando portabilidad en cualquier entorno (Windows, Linux, Mac).

*   **Network:** Todos los contenedores comparten una red interna puente de Docker.
*   **Límites de Recursos:** Cada microservicio Python está restringido a ~50MB de memoria RAM para garantizar un despliegue ligero.
*   **Volúmenes:** Se montan archivos de configuración al vuelo (Mosquitto.conf, Prometheus.yml, Alertas y Dashboards de Grafana) facilitando la edición en caliente.
