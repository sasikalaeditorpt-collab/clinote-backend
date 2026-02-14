#!/usr/bin/env bash
set -o errexit

# Update package lists
apt-get update

# Install LibreOffice (headless mode)
apt-get install -y libreoffice

# Clean up to reduce image size
apt-get clean