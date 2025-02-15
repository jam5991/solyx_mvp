#!/bin/bash
set -e

echo "Cleaning up Solyx AI development environment..."

# Remove pre-commit hooks if they exist
if [ -f ".git/hooks/pre-commit" ]; then
    pre-commit uninstall
fi

# Remove virtual environment if it exists
if [ -d "venv" ]; then
    rm -rf venv
fi

# Optionally remove requirements.txt if it was auto-generated
read -p "Do you want to remove requirements.txt? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -f requirements.txt
fi

# Optionally remove .pre-commit-config.yaml if it was auto-generated
read -p "Do you want to remove .pre-commit-config.yaml? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -f .pre-commit-config.yaml
fi

echo "Cleanup complete!"
