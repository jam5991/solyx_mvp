#!/bin/bash
set -e

# Default values
COMPONENT=${1:-all}  # all, drm, cmo, or sdn
NAMESPACE=${2:-development}  # development, staging, or production
TAIL=${3:-100}  # number of lines to show

echo "Collecting logs for Solyx AI components..."

# Function to get logs for a specific component
get_component_logs() {
    local component=$1
    echo "=== Logs for ${component} ==="
    kubectl logs -n solyx-${NAMESPACE} -l app=${component} --tail=${TAIL} --all-containers=true || echo "No logs found for ${component}"
    echo "=========================="
}

# Collect logs based on component parameter
if [ "$COMPONENT" = "all" ]; then
    for comp in "drm" "cmo" "sdn"; do
        get_component_logs $comp
    done
else
    get_component_logs $COMPONENT
fi
