#!/usr/bin/env bash
#
# Script de inicio rápido con Docker Compose
# ==========================================
# Este script facilita el uso de Vigilant con Docker para usuarios no técnicos.
#
# Uso:
#   ./docker-quick-start.sh help     # Muestra ayuda (default)
#   ./docker-quick-start.sh start    # Inicia los servicios
#   ./docker-quick-start.sh pull     # Descarga modelos de IA
#   ./docker-quick-start.sh analyze  # Muestra ejemplo de cómo ejecutar análisis
#   ./docker-quick-start.sh stop     # Detiene los servicios
#   ./docker-quick-start.sh logs     # Muestra logs (Docker/Ollama) y ruta de logs de Vigilant
#

set -euo pipefail

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para imprimir mensajes
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar que Docker Compose está instalado
if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
    DOCKER_COMPOSE="docker-compose"
else
    print_error "Docker Compose no está instalado. Por favor instalar Docker Compose primero."
    exit 1
fi

# Función para crear directorios necesarios
setup_directories() {
    print_info "Creando directorios de datos..."
    mkdir -p data/mfs data/mp4 data/pdf data/json data/tmp data/reports/md data/reports/imgs logs
    print_info "✓ Directorios creados"
}

# Función para iniciar servicios
start_services() {
    print_info "Iniciando servicios de Vigilant..."
    $DOCKER_COMPOSE up -d
    print_info "✓ Servicios iniciados"
    print_info ""
    print_info "Esperando a que Ollama esté listo..."
    sleep 10
    print_info "✓ Servicios listos"
}

# Función para descargar modelos de IA
pull_models() {
    print_info "Descargando modelos de IA (esto puede demorar varios minutos)..."
    print_info "Descargando llava:13b..."
    docker exec vigilant-ollama ollama pull llava:13b
    print_info "Descargando mistral:latest..."
    docker exec vigilant-ollama ollama pull mistral:latest
    print_info "Descargando nomic-embed-text:latest..."
    docker exec vigilant-ollama ollama pull nomic-embed-text:latest
    print_info "✓ Modelos descargados correctamente"
}

# Función para detener servicios
stop_services() {
    print_info "Deteniendo servicios..."
    $DOCKER_COMPOSE down
    print_info "✓ Servicios detenidos"
}

# Función para mostrar logs
show_logs() {
    print_info "Mostrando logs (Ctrl+C para salir)..."
    print_info "Nota: Vigilant escribe en logs/vigilant.log (en el host)."
    $DOCKER_COMPOSE logs -f
}

# Función para ejecutar un comando en el contenedor
run_command() {
    docker exec -it vigilant-app vigilant "$@"
}

# Función para mostrar ejemplo de análisis
example_analyze() {
    print_info "Ejecutando análisis de ejemplo..."
    print_warn "Asegurate de tener archivos .mfs en data/mfs/"
    print_info ""
    print_info "Comando de ejemplo:"
    echo "  docker exec -it vigilant-app vigilant analyze --prompt \"Un auto oscuro\""
    print_info ""
    print_info "Para ejecutar el análisis real, ejecutar:"
    echo "  ./docker-quick-start.sh cmd analyze --prompt \"Tu búsqueda aquí\""
}

# Función para mostrar estado de servicios
show_status() {
    print_info "Estado de servicios:"
    $DOCKER_COMPOSE ps
}

# Función para mostrar ayuda
show_help() {
    cat <<EOF
Vigilant Docker Quick Start
============================

Uso: $0 [COMANDO]

Comandos:
  start       Inicia los servicios de Vigilant
  pull        Descarga modelos de IA necesarios
	  stop        Detiene los servicios
	  restart     Reinicia los servicios
	  logs        Muestra logs (Ollama/Docker); Vigilant: logs/vigilant.log
	  status      Muestra estado de los servicios
	  analyze     Muestra ejemplo de cómo ejecutar análisis
  cmd [...]   Ejecuta un comando vigilant en el contenedor
  help        Muestra esta ayuda

Ejemplos:
  $0 start                    # Inicia servicios
  $0 pull                     # Descarga modelos
  $0 cmd convert              # Convierte archivos MFS
  $0 cmd analyze --help       # Ayuda del comando analyze

Primeros pasos:
  1. ./docker-quick-start.sh start
  2. ./docker-quick-start.sh pull
  3. Copiar archivos .mfs a data/mfs/
  4. ./docker-quick-start.sh cmd analyze --prompt "Tu búsqueda"

EOF
}

# Procesamiento de comandos
COMMAND="${1:-help}"

case "$COMMAND" in
    start)
        setup_directories
        start_services
        print_info ""
        print_info "Servicios iniciados. Próximo paso:"
        print_info "  ./docker-quick-start.sh pull    # Para descargar modelos de IA"
        ;;
    pull)
        pull_models
        ;;
    stop)
        stop_services
        ;;
    restart)
        stop_services
        start_services
        ;;
    logs)
        show_logs
        ;;
    status)
        show_status
        ;;
    analyze)
        example_analyze
        ;;
    cmd)
        shift  # Remover 'cmd'
        run_command "$@"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Comando desconocido: $COMMAND"
        print_info "Usar './docker-quick-start.sh help' para ver comandos disponibles"
        exit 1
        ;;
esac
