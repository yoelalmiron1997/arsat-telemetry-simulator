#!/bin/bash
# Script de despliegue rápido para Debian/Ubuntu
# Ejecutar con privilegios de superusuario (sudo)

set -e # Detener el script si ocurre algún error

echo "========================================================="
echo "🚀 Iniciando instalación de la Estación Terrena ARSAT"
echo "========================================================="

# 1. Actualizar el sistema
echo -e "\n📦 [1/4] Actualizando repositorios del sistema..."
apt-get update -y
apt-get install -y curl ca-certificates gnupg git

# 2. Instalar Docker y Docker Compose si no existen
if ! command -v docker &> /dev/null; then
    echo -e "\n🐳 [2/4] Docker no encontrado. Descargando e instalando Docker Engine..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
else
    echo -e "\n✅ [2/4] Docker ya está instalado en el sistema."
fi

# 3. Habilitar y arrancar el servicio de Docker
echo -e "\n⚙️ [3/4] Asegurando que el demonio de Docker esté corriendo..."
systemctl enable docker
systemctl start docker

# 4. Compilar y levantar la infraestructura
echo -e "\n🛰️ [4/4] Levantando los microservicios del Satélite ARSAT..."
# Navegamos al directorio donde se encuentra este script
cd "$(dirname "$0")" || exit

# Usamos el plugin moderno 'docker compose' (V2)
docker compose down || true # Limpiamos instalaciones previas si las hubiera
docker compose up -d --build

echo "========================================================="
echo "✅ ¡Despliegue Completado Exitosamente!"
echo "========================================================="
echo "🌍 Interfaz de Monitoreo (Grafana): http://<IP_DE_ESTE_SERVIDOR>:3000"
echo "📈 Base de Datos (Prometheus)   : http://<IP_DE_ESTE_SERVIDOR>:9090"
echo "🔐 Grafana Login -> Usuario: admin | Clave: admin"
echo "========================================================="
