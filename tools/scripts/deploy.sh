#!/bin/bash
set -e

echo "Deploying Solyx AI core components..."

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo "kubectl is required but not installed."
    exit 1
fi

# Check if kind is installed
if ! command -v kind &> /dev/null; then
    echo "kind is required but not installed."
    echo "Please install kind: https://kind.sigs.k8s.io/docs/user/quick-start/"
    exit 1
fi

# Check if cluster exists and create if it doesn't
if ! kind get clusters | grep -q "solyx-dev"; then
    echo "Creating local Kubernetes cluster with kind..."
    kind create cluster --name solyx-dev
    echo "Waiting for cluster to be ready..."
    sleep 10
fi

# Ensure we're using the kind cluster context
kubectl config use-context kind-solyx-dev

# Set environment
ENV=${1:-development}
NAMESPACE="solyx-${ENV}"

# Create namespace if it doesn't exist
echo "Creating namespace ${NAMESPACE}..."
kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

# Create placeholder deployments for testing
echo "Creating test deployments..."
for component in "drm" "cmo" "sdn"; do
    echo "Deploying ${component} test deployment..."
    kubectl create deployment ${component} \
        --image=nginx:alpine \
        --namespace=${NAMESPACE} \
        --dry-run=client -o yaml | kubectl apply -f -
done

# Wait for deployments to be ready
echo "Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=60s deployment --all -n ${NAMESPACE}

echo "Deployment complete! Component status:"
kubectl get pods -n ${NAMESPACE}
