# Solyx AI Workflows

This directory contains GitHub Actions workflows that automate various development and maintenance tasks for the Solyx AI project.

## Workflows Overview

### 1. CI Pipeline (`ci.yml`)

Handles continuous integration tasks including testing, building, and security scanning.

#### Triggers
- Push events to `main` and `dev` branches
- Pull requests to `main` and `dev` branches

#### Jobs
- **Code Quality**
  - Runs linters and formatters (black, isort, flake8, mypy)
  - Ensures consistent code style and quality

- **Unit Tests**
  - Executes Python unit tests
  - Generates and uploads coverage reports

- **Integration Tests**
  - Sets up k3d cluster for Kubernetes testing
  - Runs integration test suite

- **Build** (only on `main` branch)
  - Builds Docker images for all components:
    - DRM (Distributed Resource Manager)
    - CMO (Cluster Management Orchestrator)
    - SDN Controller
  - Pushes images to GitHub Container Registry with tags:
    - `latest`
    - Git SHA (e.g., `ghcr.io/repo/component:abc123`)

- **Security Scan**
  - Uses Trivy to scan Docker images
  - Checks for known vulnerabilities
  - Fails on HIGH and CRITICAL severity issues

### 2. Dependency Updates (`dependencies.yml`)

Automates dependency management for the project.

#### Triggers
- Weekly schedule (Sundays at 00:00 UTC)
- Manual trigger via GitHub UI

#### Process
1. Updates Python dependencies using pip-tools
2. Creates a pull request to `dev` branch
3. Includes updated dependency files
4. Automatically cleans up branches after merge

## Usage

These workflows run automatically based on their triggers. However, you can also:

1. View workflow runs in the GitHub Actions tab
2. Manually trigger the dependency update workflow
3. Download artifacts (like test coverage reports) from workflow runs

## Monitoring

- Check the "Actions" tab in GitHub to monitor workflow runs
- Failed workflows will notify via GitHub notifications
- Security scan results are available in workflow logs

## Contributing

When contributing to the project:
1. Ensure your code passes all CI checks
2. Review dependency update PRs when they appear
3. Check security scan results for any new vulnerabilities

For workflow modifications:
1. Test changes in a fork first
2. Ensure secrets and permissions are properly configured
3. Update this README when adding new workflows 