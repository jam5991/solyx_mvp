#!/bin/bash
set -e

echo "Setting up Solyx AI development environment..."

# Check if conda is installed
if ! command -v conda &> /dev/null; then
    echo "Conda is required but not installed."
    echo "Please install Miniconda or Anaconda from:"
    echo "https://docs.conda.io/projects/conda/en/latest/user-guide/install/"
    exit 1
fi

# Initialize conda for the current shell
echo "Initializing conda..."
conda init bash
# For Windows Git Bash specifically
if [[ "$OSTYPE" == "msys" ]]; then
    conda init bash
    echo "Please close and reopen Git Bash, then run this script again."
    exit 0
fi

# Set environment name
ENV_NAME="solyx"

# Remove existing environment if it exists
conda remove --name $ENV_NAME --all -y 2>/dev/null || true

# Create new conda environment
echo "Creating conda environment: $ENV_NAME"
conda create -n $ENV_NAME python=3.10 -y

# Activate conda environment
eval "$(conda shell.bash hook)"
conda activate $ENV_NAME

# Install base requirements with conda
echo "Installing base requirements..."
conda install -y pytest pytest-cov pip

# Install Kind if not already installed
if ! command -v kind &> /dev/null; then
    echo "Installing Kind..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        brew install kind
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
        chmod +x ./kind
        sudo mv ./kind /usr/local/bin/
    elif [[ "$OSTYPE" == "msys" ]]; then
        # Windows (Git Bash)
        echo "Please install Kind manually on Windows:"
        echo "1. Download from: https://kind.sigs.k8s.io/dl/v0.20.0/kind-windows-amd64"
        echo "2. Rename to kind.exe"
        echo "3. Move to a directory in your PATH"
        read -p "Press enter to continue after installing Kind..."
    fi
fi

# Install pre-commit using pip
pip install pre-commit

# Install requirements.txt if it exists
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
else
    echo "No requirements.txt found. Creating basic requirements file..."
    cat > requirements.txt << EOF
pytest>=7.0.0
pytest-cov>=4.0.0
pre-commit>=3.0.0
kubernetes>=28.1.0
docker>=6.1.0
requests>=2.31.0
# Development tools
kind>=0.20.0  # For local Kubernetes clusters
kubectl>=1.28.0  # For managing Kubernetes clusters
EOF
    pip install -r requirements.txt
fi

# Verify Kind installation
if command -v kind &> /dev/null; then
    echo "Kind version: $(kind --version)"
else
    echo "Warning: Kind installation not found in PATH"
fi

# Setup pre-commit hooks if .pre-commit-config.yaml exists
if [ -f ".pre-commit-config.yaml" ]; then
    echo "Setting up pre-commit hooks..."
    pre-commit install
else
    echo "No .pre-commit-config.yaml found. Creating basic config..."
    cat > .pre-commit-config.yaml << EOF
repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
    -   id: trailing-whitespace
    -   id: end-of-file-fixer
    -   id: check-yaml
    -   id: check-added-large-files
-   repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
    -   id: black
EOF
    pre-commit install
fi

echo "Development environment setup complete!"
echo "To activate the environment, run: conda activate $ENV_NAME"
