#!/bin/bash
set -e

echo "Cleaning up Solyx AI development environment..."

# Set environment
ENV=${1:-development}
NAMESPACE="solyx-${ENV}"

# Function to safely delete resources
safe_delete() {
    local resource=$1
    echo "Cleaning up ${resource}..."
    kubectl delete -k deploy/kubernetes/${resource}/overlays/${ENV} --ignore-not-found=true
}

# Clean up components in reverse order
components=("sdn" "cmo" "drm")
for component in "${components[@]}"; do
    safe_delete ${component}
done

# Remove namespace
echo "Removing namespace ${NAMESPACE}..."
kubectl delete namespace ${NAMESPACE} --ignore-not-found=true

# Clean up monitoring stack
echo "Cleaning up monitoring stack..."
kubectl delete namespace monitoring --ignore-not-found=true

# Optional: Remove kind cluster
if [ "$2" == "--full" ]; then
    echo "Removing kind cluster..."
    kind delete cluster --name solyx-dev
fi

echo "Cleanup complete!"
