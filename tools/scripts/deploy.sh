#!/bin/bash
set -e

echo "Deploying Solyx AI components..."

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

# Define component configurations
declare -A PORTS
PORTS["drm"]=8000
PORTS["cmo"]=8082
PORTS["sdn"]=8083

# Build and deploy DRM Core
echo "Building DRM Core..."
docker build -t solyx/drm-core:latest ./drm-core
docker push solyx/drm-core:latest  # If using a registry

# Build and deploy CMO Service
echo "Building CMO Service..."
docker build -t solyx/cmo-service:latest ./cmo-service
docker push solyx/cmo-service:latest  # If using a registry

# Create secrets
echo "Creating secrets..."
kubectl create secret generic gpu-provider-secrets \
    --namespace=${NAMESPACE} \
    --from-file=./drm-core/config.env \
    --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic db-credentials \
    --namespace=${NAMESPACE} \
    --from-file=./cmo-service/config.env \
    --dry-run=client -o yaml | kubectl apply -f -

# Create deployments and services for each component
echo "Creating deployments and services..."
for component in "${!PORTS[@]}"; do
    echo "Deploying ${component}..."

    PORT=${PORTS[$component]}

    if [ "${component}" = "drm" ]; then
        # Special handling for DRM component
        echo "Building DRM container..."
        docker build -t solyx/drm:latest ./drm-core

        # Load the image into kind cluster
        echo "Loading DRM image into kind cluster..."
        kind load docker-image solyx/drm:latest --name solyx-dev

        # Apply DRM-specific deployment
        kubectl apply -f ./drm-core/kubernetes/drm-deployment.yaml
    else
        # Default handling for other components
        kubectl create deployment ${component} \
            --image=nginx:alpine \
            --namespace=${NAMESPACE} \
            --dry-run=client -o yaml | kubectl apply -f -
    fi

    # Create service
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: ${component}
  namespace: ${NAMESPACE}
spec:
  selector:
    app: ${component}
  ports:
  - port: ${PORT}
    targetPort: ${component == "drm" ? PORT : 80}
    protocol: TCP
  type: ClusterIP
EOF

    # Add labels to deployment for service selection
    kubectl label deployment ${component} -n ${NAMESPACE} app=${component} --overwrite
done

# Apply deployments
echo "Applying deployments..."
kubectl apply -f ./cmo-service/kubernetes/cmo-deployment.yaml

# Wait for deployments to be ready
echo "Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=60s deployment --all -n ${NAMESPACE}

echo "Deployment complete! Component status:"
echo -e "\nPods:"
kubectl get pods -n ${NAMESPACE}
echo -e "\nServices:"
kubectl get svc -n ${NAMESPACE}

echo -e "\nAccess URLs (after port-forwarding):"
for component in "${!PORTS[@]}"; do
    echo "${component}: http://localhost:${PORTS[$component]}"
done

echo -e "\nTo port-forward a service, use:"
echo "kubectl port-forward -n ${NAMESPACE} svc/<service-name> <local-port>:<service-port>"
echo "Example: kubectl port-forward -n ${NAMESPACE} svc/drm ${PORTS[drm]}:${PORTS[drm]}"
