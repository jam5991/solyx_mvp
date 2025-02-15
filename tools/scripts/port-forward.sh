#!/bin/bash
set -e

# Default values
COMPONENT=${1:-drm}  # drm, cmo, sdn, grafana, or prometheus
NAMESPACE=${2:-solyx-development}  # solyx-development, monitoring
LOCAL_PORT=${3}  # If not provided, will use the default port for the component

echo "Setting up port forwarding for ${COMPONENT}..."

# Define service names and their ports for all components
declare -A SERVICE_MAP
# Solyx components
SERVICE_MAP["drm"]="drm:8081"
SERVICE_MAP["cmo"]="cmo:8082"
SERVICE_MAP["sdn"]="sdn:8083"
# Monitoring components
SERVICE_MAP["grafana"]="grafana:80"
SERVICE_MAP["prometheus"]="prometheus-server:80"
SERVICE_MAP["alertmanager"]="prometheus-alertmanager:9093"

# Get the service and port configuration
SERVICE_CONFIG=${SERVICE_MAP[$COMPONENT]}

if [ -z "$SERVICE_CONFIG" ]; then
    echo "Unknown component: ${COMPONENT}"
    echo "Available components:"
    echo "Solyx components (namespace: solyx-development):"
    echo "  - drm     (port: 8081)"
    echo "  - cmo     (port: 8082)"
    echo "  - sdn     (port: 8083)"
    echo "Monitoring components (namespace: monitoring):"
    echo "  - grafana      (port: 80)"
    echo "  - prometheus   (port: 80)"
    echo "  - alertmanager (port: 9093)"
    exit 1
fi

# Split service name and port
SERVICE_NAME=$(echo $SERVICE_CONFIG | cut -d: -f1)
TARGET_PORT=$(echo $SERVICE_CONFIG | cut -d: -f2)

# If LOCAL_PORT not provided, use TARGET_PORT
if [ -z "$LOCAL_PORT" ]; then
    LOCAL_PORT=$TARGET_PORT
fi

# Adjust namespace based on component
if [[ "$COMPONENT" == "grafana" || "$COMPONENT" == "prometheus" || "$COMPONENT" == "alertmanager" ]]; then
    NAMESPACE="monitoring"
fi

# Verify service exists
if ! kubectl get svc -n ${NAMESPACE} ${SERVICE_NAME} &>/dev/null; then
    echo "Service ${SERVICE_NAME} not found in namespace ${NAMESPACE}"
    echo "Available services in ${NAMESPACE}:"
    kubectl get svc -n ${NAMESPACE}
    exit 1
fi

# Start port forwarding
echo "Forwarding local port ${LOCAL_PORT} to ${SERVICE_NAME}:${TARGET_PORT}"
echo "Access URL: http://localhost:${LOCAL_PORT}"
kubectl port-forward -n ${NAMESPACE} svc/${SERVICE_NAME} ${LOCAL_PORT}:${TARGET_PORT}
