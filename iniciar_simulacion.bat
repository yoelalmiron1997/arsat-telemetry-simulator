@echo off
title Simulador Satelital ARSAT
color 0A

echo =========================================================
echo    Iniciando Mision Satelital ARSAT (Simulacion)
echo =========================================================
echo.

:: Verificar si Docker está corriendo
echo [1/3] Verificando estado de Docker...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [ERROR CRITICO] Docker Desktop no esta ejecutandose o no esta instalado.
    echo Por favor, abre Docker Desktop en tu computadora e intentalo de nuevo.
    echo.
    pause
    exit /b 1
)
echo [OK] Docker esta funcionando correctamente.
echo.

:: Levantar los servicios
echo [2/3] Construyendo e iniciando los microservicios espaciales...
echo Esto puede tomar unos segundos...
docker compose down
docker compose up -d --build
echo.

:: Finalización
echo [3/3] Servicios iniciados exitosamente.
echo.
echo =========================================================
echo            SISTEMA ONLINE Y OPERATIVO
echo =========================================================
echo Panel de Control Grafana : http://localhost:3000
echo Base de Datos Prometheus : http://localhost:9090
echo.
echo Credenciales de Grafana  : admin / admin
echo =========================================================
echo.
echo Presiona cualquier tecla para abrir el navegador web...
pause >nul

:: Abrir el navegador por defecto
start http://localhost:3000

exit
