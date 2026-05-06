# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-04-23

### Added
- Arquitectura completa basada en microservicios pub/sub (MQTT).
- Simulación del Subsistema de Energía (EPS).
- Simulación del Subsistema Térmico (TCS).
- Simulación del Subsistema de Control de Actitud y Órbita (AOCS) con métricas de Star Tracker y GPS.
- Simulación de la Carga Útil (Payload) de comunicaciones.
- Funcionalidad pedagógica: Codificación y decodificación de tramas CCSDS simuladas en formato Hexadecimal usando la librería `struct`.
- Estación Terrena (`ground_station.py`) para suscribirse al broker MQTT, decodificar tramas e ingestar a Prometheus vía `prometheus_client`.
- Archivo `docker-compose.yml` optimizado para equipos de bajos recursos (Netbooks gubernamentales) utilizando imágenes Alpine y límites estrictos de RAM (deploy.resources.limits).
- Archivo base `Dockerfile` usando Python 3.11-alpine.
- Configuración de Mosquitto (`mosquitto.conf`) para acceso anónimo en red local.
- Configuración de Prometheus (`prometheus.yml`) apuntando al Gateway.
- Documentación inicial (`README.md`) explicando la arquitectura, el flujo de tramas y las instrucciones de despliegue.
