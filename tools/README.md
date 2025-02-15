# Solyx AI Tools and Setup

Welcome to the Solyx AI Tools & Setup repository. This document provides a complete overview of the scripts, configurations, and resources within the tools folder to help manage and streamline the Solyx AI development environment.

## Getting Started

Follow these steps to set up your Solyx AI development environment:

1. Prerequisite Check:
   - Ensure that Conda is installed and properly configured
   - Verify your shell environment (Terminal on macOS/Linux or Git Bash on Windows)

2. Directory Structure Setup:
   ```bash
   sh tools/setup/create_dirs.sh
   ```
   Creates the necessary directory structure for the project, including:
   - tools/setup: Contains setup and configuration scripts
   - tools/scripts: Contains operational scripts
   - deploy/kubernetes: Contains Kubernetes manifests with separate overlays for different environments

3. Environment Setup:
   ```bash
   sh tools/setup/install.sh
   ```
   Sets up the complete development environment:
   - Creates a new Conda environment named 'solyx'
   - Installs Python 3.10 and essential packages
   - Sets up Kind for local Kubernetes clusters
   - Installs and configures pre-commit hooks
   - Creates basic requirements.txt if not present

4. Environment Configuration:
   ```bash
   sh tools/setup/configure.sh [environment]
   ```
   Configures the environment-specific settings:
   - Sets up environment variables
   - Configures kubectl context
   - Creates necessary local directories (~/.solyx)
   - Default environment is 'development' if not specified

5. Development Cluster Setup:
   ```bash
   sh tools/scripts/dev-setup.sh
   ```
   Initializes the local development environment:
   - Creates a Kind cluster named 'solyx-dev'
   - Sets up monitoring stack with Prometheus and Grafana
   - Configures Helm repositories
   - Saves Grafana admin credentials

6. Run Tests:
   ```bash
   sh tools/scripts/test.sh
   ```
   Executes the test suite:
   - Runs unit tests (tests/unit)
   - Runs integration tests (tests/integration)
   - Runs E2E tests (tests/e2e)
   - Generates test reports in test-reports directory

7. Deploy Components:
   ```bash
   sh tools/scripts/deploy.sh [environment]
   ```
   Deploys the Solyx AI components:
   - Creates/verifies Kind cluster
   - Sets up namespace for specified environment
   - Deploys core components (DRM, CMO, SDN)
   - Default environment is 'development' if not specified

8. Cleanup:
   ```bash
   sh tools/scripts/cleanup.sh [environment] [--full]
   ```
   Cleans up the deployment:
   - Removes deployed components in reverse order
   - Deletes environment-specific namespace
   - Removes monitoring stack
   - Optional '--full' flag removes the entire Kind cluster

9. Uninstall:
   ```bash
   sh tools/setup/uninstall.sh
   ```
   Removes the development environment:
   - Uninstalls pre-commit hooks
   - Removes virtual environment
   - Optionally removes generated config files
