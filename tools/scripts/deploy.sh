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

# Define component configurations
declare -A PORTS
PORTS["drm"]=8081
PORTS["cmo"]=8082
PORTS["sdn"]=8083

# Create deployments and services for each component
echo "Creating deployments and services..."
for component in "${!PORTS[@]}"; do
    echo "Deploying ${component}..."

    PORT=${PORTS[$component]}

    # Create deployment
    kubectl create deployment ${component} \
        --image=nginx:alpine \
        --namespace=${NAMESPACE} \
        --dry-run=client -o yaml | kubectl apply -f -

    # Delete existing service if it exists
    kubectl delete service ${component} -n ${NAMESPACE} --ignore-not-found

    # Create service with both service port and target port set to the same value
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
    targetPort: 80
    protocol: TCP
  type: ClusterIP
EOF

    # Add labels to deployment for service selection
    kubectl label deployment ${component} -n ${NAMESPACE} app=${component} --overwrite
done

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
