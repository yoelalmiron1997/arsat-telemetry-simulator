"""
Generador del "historial" de telemetría usado por los servicios mock
(src/mock/mock_*.py) para el deploy público.

Reproduce EXACTAMENTE el mismo algoritmo y los mismos rangos físicos que
los servicios reales (power_service.py, thermal_service.py, aocs_service.py,
payload_service.py), pero con una semilla fija (`random.seed(42)`), de
forma que el resultado es 100% reproducible: cualquiera que corra este
script obtiene el mismo historial, y cualquiera que vea el deploy público
ve siempre la misma secuencia de valores y la misma anomalía en el mismo
momento del ciclo.

N_SAMPLES = 90 muestras a intervalos de 2s (igual que los servicios
reales) = 180s de historial = 6 ciclos completos de anomalía del EPS
(cada ciclo son 15 lecturas / 30s, de las cuales 5 son anómalas).

Los servicios mock (mock_power.py, etc.) recorren esta lista en loop
infinito. Al llegar al final vuelven al índice 0 — ese es el "rollback":
el demo público siempre repite la misma pasada orbital con la misma
anomalía, en vez de mostrar ruido puramente aleatorio sin fin.

Para regenerar el historial (por ejemplo, con más muestras o rangos
distintos), correr:
    python generate_history.py
"""
import json
import os
import random
import struct
import binascii

random.seed(42)

N_SAMPLES = 90  # 90 * 2s = 180s de historial por vuelta de loop
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "history")


def generar_eps():
    historial = []
    counter = 0
    for _ in range(N_SAMPLES):
        counter += 1
        # Misma lógica exacta que power_service.py::get_telemetry()
        if counter % 15 < 5:
            voltage = round(random.uniform(20.0, 21.0), 2)
            current = round(random.uniform(10.0, 15.0), 2)
            battery = round(random.uniform(10.0, 15.0), 2)
        else:
            voltage = round(random.uniform(27.5, 28.5), 2)
            current = round(random.uniform(2.0, 5.5), 2)
            battery = round(random.uniform(85.0, 100.0), 2)
        historial.append({"voltage": voltage, "current": current, "battery": battery})
    return historial


def generar_tcs():
    historial = []
    for _ in range(N_SAMPLES):
        # Misma lógica exacta que thermal_service.py::get_telemetry()
        temp_solar = round(random.uniform(-100.0, 100.0), 2)
        temp_battery = round(random.uniform(10.0, 25.0), 2)
        temp_payload = round(random.uniform(15.0, 35.0), 2)
        historial.append({
            "temp_solar": temp_solar,
            "temp_battery": temp_battery,
            "temp_payload": temp_payload,
        })
    return historial


def generar_aocs():
    historial = []
    # Mismos valores base que aocs_service.py
    base_lat = -34.0
    base_lon = -71.8
    base_alt = 35786.0
    for _ in range(N_SAMPLES):
        pitch = round(random.uniform(-0.05, 0.05), 4)
        roll = round(random.uniform(-0.05, 0.05), 4)
        yaw = round(random.uniform(-0.05, 0.05), 4)
        stars_tracked = random.randint(4, 12)

        base_lon += 1.5
        base_lat += random.uniform(-0.1, 0.1)
        if base_lon > 180:
            base_lon -= 360

        lat = round(base_lat, 4)
        lon = round(base_lon, 4)
        alt = round(base_alt + random.uniform(-1.0, 1.0), 2)

        historial.append({
            "pitch": pitch, "roll": roll, "yaw": yaw,
            "stars_tracked": stars_tracked,
            "lat": lat, "lon": lon, "alt": alt,
        })
    return historial


def generar_payload():
    historial = []
    for _ in range(N_SAMPLES):
        # Misma lógica exacta que payload_service.py::get_telemetry()
        status = 1 if random.random() > 0.05 else 0
        downlink = round(random.uniform(500.0, 1500.0), 2) if status == 1 else 0.0
        uplink = round(random.uniform(200.0, 600.0), 2) if status == 1 else 0.0
        historial.append({"status": status, "downlink": downlink, "uplink": uplink})
    return historial


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    datasets = {
        "eps_history.json": generar_eps(),
        "tcs_history.json": generar_tcs(),
        "aocs_history.json": generar_aocs(),
        "payload_history.json": generar_payload(),
    }

    for filename, data in datasets.items():
        path = os.path.join(OUTPUT_DIR, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Generado {path} ({len(data)} muestras)")


if __name__ == "__main__":
    main()
