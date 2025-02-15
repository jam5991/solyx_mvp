#!/bin/bash
set -e

NAMESPACE=${1:-development}

echo "Checking Solyx AI component status..."

# Check pods status
echo "=== Pods Status ==="
for comp in "drm" "cmo" "sdn"; do
    echo "--- ${comp} ---"
    kubectl get pods -n solyx-${NAMESPACE} -l app=${comp} -o wide
done

# Check services status
echo -e "\n=== Services Status ==="
kubectl get services -n solyx-${NAMESPACE}

# Check deployments status
echo -e "\n=== Deployments Status ==="
kubectl get deployments -n solyx-${NAMESPACE}

# Check resource usage
echo -e "\n=== Resource Usage ==="
kubectl top pods -n solyx-${NAMESPACE} || echo "Metrics server not available"
