#!/bin/bash
# Create required directories
mkdir -p tools/setup
mkdir -p tools/scripts
mkdir -p deploy/kubernetes/{drm,cmo,sdn}/overlays/{development,staging,production}
chmod 755 tools/setup tools/scripts

echo "Directory structure created successfully!"
