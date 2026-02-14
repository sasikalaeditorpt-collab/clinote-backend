#!/usr/bin/env bash
set -o errexit

# Install LibreOffice at runtime (allowed on Render)
apt-get update || true
apt-get install -y libreoffice || true

# Start the app
uvicorn typing_engine_api:app --host 0.0.0.0 --port 10000