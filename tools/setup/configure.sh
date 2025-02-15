#!/bin/bash
set -e

echo "Configuring Solyx AI environment..."

# Set environment variables
export SOLYX_ENV=${1:-development}
export SOLYX_NAMESPACE="solyx-${SOLYX_ENV}"

# Create kubeconfig if not exists
if [ ! -f ~/.kube/config ]; then
    mkdir -p ~/.kube
    touch ~/.kube/config
fi

# Configure kubectl context
if [ "${SOLYX_ENV}" = "development" ]; then
    # Setup local development context
    kubectl config set-context solyx-dev --namespace=${SOLYX_NAMESPACE}
    kubectl config use-context solyx-dev
fi

# Create necessary directories
mkdir -p ~/.solyx/config
mkdir -p ~/.solyx/logs

echo "Configuration complete for ${SOLYX_ENV} environment!"
