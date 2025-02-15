#!/bin/bash
set -e

echo "Running Solyx AI test suites..."

# Create test-reports directory if it doesn't exist
mkdir -p test-reports

# Activate conda environment if it exists
if command -v conda &> /dev/null; then
    eval "$(conda shell.bash hook)"
    conda activate solyx 2>/dev/null || echo "Conda environment 'solyx' not found"
fi

# Function to check if directory has test files
has_tests() {
    local dir=$1
    if [ -d "$dir" ] && [ "$(ls -A $dir)" ]; then
        return 0  # Directory exists and is not empty
    fi
    return 1  # Directory doesn't exist or is empty
}

# Run unit tests
echo "Running unit tests..."
if has_tests "tests/unit"; then
    python -m pytest tests/unit/ -v --junitxml=test-reports/unit.xml
else
    echo "No unit tests found in tests/unit/"
fi

# Run integration tests
echo "Running integration tests..."
if has_tests "tests/integration"; then
    python -m pytest tests/integration/ -v --junitxml=test-reports/integration.xml
else
    echo "No integration tests found in tests/integration/"
fi

# Run E2E tests
echo "Running E2E tests..."
if has_tests "tests/e2e"; then
    python -m pytest tests/e2e/ -v --junitxml=test-reports/e2e.xml
else
    echo "No E2E tests found in tests/e2e/"
fi

echo "Test suite execution completed!"
