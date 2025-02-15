# Solyx AI Tools and Setup

Welcome to the Solyx AI Tools & Setup repository. This document provides a complete overview of the scripts, configurations, and resources within the tools folder to help manage and streamline the Solyx AI development environment.

## Folder Structure and Key Components

- **scripts/**
  - This directory houses a collection of scripts that streamline various development and operational tasks:
    - **dev-setup.sh**: Initializes your local Kubernetes cluster using Kind, sets up and updates Helm repositories, and deploys a monitoring stack (Prometheus and Grafana). It also retrieves the Grafana admin password, ensuring a fully configured environment for development and testing.
    - **cleanup.sh**: Cleans up the development environment by removing temporary resources, deleting Kubernetes namespaces, and optionally dismantling the Kind cluster, maintaining a tidy system state.
    - **test.sh**: Executes the project's test suite, running unit and integration tests to verify code integrity and ensure that recent changes meet quality standards.
    - **deploy.sh**: Manages the deployment process by automating build, containerization, and the deployment of the application to staging or production environments, thereby simplifying the release cycle.

- **setup/**
  - Contains essential scripts used for configuring and managing your development environment:
    - **configure.sh**: Customizes environment settings and prepares necessary configuration files.
    - **create_dirs.sh**: Automatically creates the required directory structure and file locations.
    - **install.sh**: Installs dependencies, sets up virtual environments (e.g., with Conda), and initializes tools for development.
    - **uninstall.sh**: Cleans up by reverting installations, removing configurations, and deleting created directories.

- **Configuration Files and Resources**
  - **kind-config.yaml**: Provides the specific configuration for the local Kind cluster.
  - **grafana_admin_password.txt**: Stores the Grafana admin password generated during the deployment of the monitoring stack.

## Getting Started

Follow these detailed steps to set up, test, deploy, and clean up your Solyx AI development environment. It is recommended to run the scripts in the order outlined below:

1. Prerequisite Check:
   - Ensure that Conda, Kind, and Helm are installed and properly configured on your system.
   - Verify that your shell environment (e.g., Terminal on macOS/Linux or Git Bash on Windows) is set up to execute Bash scripts.

2. Environment Setup:
   - From the root of your project, execute the installation script to configure the necessary dependencies and create a dedicated Conda environment:
     ```bash
     sh tools/setup/install.sh
     ```
   - This script will:
     - Check for Conda and initialize it.
     - Create (or refresh) the "solyx" Conda environment with Python 3.10.
     - Install essential packages (e.g., pytest, pre-commit) and other dependencies.
     - Install Kind if it isn't already available on your system.

3. Local Kubernetes Cluster Initialization:
   - Once the environment is set up, launch your local development Kubernetes cluster by executing:
     ```bash
     sh tools/scripts/dev-setup.sh
     ```
   - This script will:
     - Confirm that Kind is installed.
     - Create a Kind-based Kubernetes cluster using the configuration defined in tools/kind-config.yaml (if the cluster isn't already running).
     - Add and update Helm repositories for Prometheus and Grafana.
     - Deploy a monitoring stack (Prometheus and Grafana) and automatically retrieve the Grafana admin password.

4. (Optional) Testing:
   - To ensure that your setup is functioning as expected, execute the test suite by running:
         sh tools/scripts/test.sh
   - This step will run unit and integration tests to verify code quality and environment consistency.

5. (Optional) Deployment:
   - When you're ready to push your application to a staging or production environment, initiate the deployment process by running:
         sh tools/scripts/deploy.sh
   - This script automates the build, containerization, and deployment procedures.

6. Cleanup:
   - After development, testing, or deployment, clean up any temporary resources and reset your environment by running:
         sh tools/scripts/cleanup.sh
   - This final step removes temporary files, deletes any created Kubernetes namespaces, and, if necessary, dismantles the Kind cluster to maintain a tidy system state.
