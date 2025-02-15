#!/bin/bash
set -e

echo "Setting up local development cluster..."

# Check if kind is installed
if ! command -v kind &> /dev/null; then
    echo "kind is not installed. Please install kind first."
    exit 1
fi

# Create local cluster if it doesn't exist
if ! kind get clusters | grep -q "solyx-dev"; then
    kind create cluster --config tools/kind-config.yaml
fi

# Install Helm repositories
echo "Setting up Helm repositories..."
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Create monitoring namespace
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

# Install monitoring stack
echo "Installing monitoring stack..."
helm upgrade --install prometheus prometheus-community/prometheus \
    --namespace monitoring \
    --set server.persistentVolume.enabled=false

helm upgrade --install grafana grafana/grafana \
    --namespace monitoring \
    --set persistence.enabled=false

# Get Grafana admin password and save to a file
GRAFANA_PASSWORD=$(kubectl get secret --namespace monitoring grafana -o jsonpath="{.data.admin-password}" | base64 --decode)
echo "Grafana admin password: $GRAFANA_PASSWORD"
echo "$GRAFANA_PASSWORD" > grafana_admin_password.txt
echo "Grafana admin password saved to grafana_admin_password.txt"

echo "Development cluster setup complete!"
