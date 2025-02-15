#!/bin/bash
set -e

COMPONENT=${1:-all}  # all, drm, cmo, or sdn
NAMESPACE=${2:-development}
CONFIG_PATH=${3:-"config/default.yaml"}

echo "Updating configuration for Solyx AI components..."

# Function to update config for a component
update_component_config() {
    local component=$1
    echo "Updating ${component} configuration..."

    # Update ConfigMap
    kubectl create configmap ${component}-config \
        --from-file=${CONFIG_PATH} \
        -n solyx-${NAMESPACE} \
        --dry-run=client -o yaml | kubectl apply -f -

    # Restart pods to pick up new config
    kubectl rollout restart deployment ${component} -n solyx-${NAMESPACE}

    # Wait for rollout to complete
    kubectl rollout status deployment ${component} -n solyx-${NAMESPACE}
}

# Update configs based on component parameter
if [ "$COMPONENT" = "all" ]; then
    for comp in "drm" "cmo" "sdn"; do
        update_component_config $comp
    done
else
    update_component_config $COMPONENT
fi

echo "Configuration update complete!"
