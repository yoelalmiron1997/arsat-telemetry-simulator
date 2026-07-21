*** Settings ***
Documentation     Integration Testing — valida el flujo completo de telemetría:
...               Satélite (trama hex) -> Broker MQTT -> Ground Station (decodificador)
...               -> Métrica Prometheus, usando valores deterministas inyectados
...               directamente por el test (sin depender del generador aleatorio).
Library           libraries/ArsatMqttLibrary.py
Library           Collections

*** Variables ***
${PROPAGATION_DELAY}    2s

*** Test Cases ***
Trama EPS Se Decodifica Correctamente End To End
    [Documentation]    Publica una trama EPS conocida y verifica que la
    ...    Ground Station la decodifica y expone en Prometheus con el
    ...    valor exacto (sin pérdida de precisión relevante).
    [Tags]    integration    eps
    Publish Eps Frame    voltage=27.90    current=3.40    battery=88.50
    Sleep    ${PROPAGATION_DELAY}
    ${voltage}=    Get Metric Value    arsat_eps_voltage_v
    ${current}=    Get Metric Value    arsat_eps_current_a
    ${battery}=    Get Metric Value    arsat_eps_battery_percent
    Should Be True    ${voltage} > 27.89 and ${voltage} < 27.91
    Should Be True    ${current} > 3.39 and ${current} < 3.41
    Should Be True    ${battery} > 88.49 and ${battery} < 88.51

Trama TCS Se Decodifica Correctamente End To End
    [Documentation]    Idem anterior, para el subsistema térmico.
    [Tags]    integration    tcs
    Publish Tcs Frame    temp_solar=45.20    temp_battery=12.10    temp_payload=30.75
    Sleep    ${PROPAGATION_DELAY}
    ${solar}=    Get Metric Value    arsat_tcs_solar_temp_c
    ${bat}=    Get Metric Value    arsat_tcs_battery_temp_c
    ${pay}=    Get Metric Value    arsat_tcs_payload_temp_c
    Should Be True    ${solar} > 45.19 and ${solar} < 45.21
    Should Be True    ${bat} > 12.09 and ${bat} < 12.11
    Should Be True    ${pay} > 30.74 and ${pay} < 30.76

Trama AOCS Se Decodifica Correctamente End To End
    [Documentation]    Valida el subsistema de orientación, incluyendo el
    ...    campo entero (estrellas fijadas por el Star Tracker).
    [Tags]    integration    aocs
    Publish Aocs Frame    pitch=1.5    roll=-0.8    yaw=179.9
    ...    stars_tracked=6    lat=-34.6    lon=-58.4    alt_km=35786.0
    Sleep    ${PROPAGATION_DELAY}
    ${stars}=    Get Metric Value    arsat_aocs_stars_tracked
    ${lat}=    Get Metric Value    arsat_aocs_gps_lat
    Should Be Equal As Numbers    ${stars}    6
    Should Be True    ${lat} > -34.61 and ${lat} < -34.59

Trama De Payload Con Falla Se Refleja Como Estado 0
    [Documentation]    Caso de negativo/falla: el transponder reporta
    ...    estado caído (0) y se espera que la métrica lo refleje así,
    ...    ya que Prometheus usará este valor para disparar la alerta
    ...    "PayloadOffline" (ver tests/regression).
    [Tags]    integration    payload    negative-case
    Publish Payload Frame    status=0    downlink_mbps=0.0    uplink_mbps=0.0
    Sleep    ${PROPAGATION_DELAY}
    ${status}=    Get Metric Value    arsat_payload_status
    Should Be Equal As Numbers    ${status}    0

Trama De Payload Nominal Se Refleja Como Estado 1
    [Documentation]    Caso positivo/control: confirma que el mismo
    ...    pipeline también reporta correctamente el estado sano,
    ...    para no tener un test que solo valide el camino de falla.
    [Tags]    integration    payload
    Publish Payload Frame    status=1    downlink_mbps=120.5    uplink_mbps=45.2
    Sleep    ${PROPAGATION_DELAY}
    ${status}=    Get Metric Value    arsat_payload_status
    Should Be Equal As Numbers    ${status}    1
