#!/bin/bash
# ChromeDriver installation script for production environments
# This script installs Chrome and ChromeDriver in Docker/Kubernetes containers

set -e

echo "Installing Google Chrome and ChromeDriver..."

# Install dependencies
apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    ca-certificates

# Add Google Chrome repository
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list

# Install Google Chrome
apt-get update && apt-get install -y google-chrome-stable

# Verify Chrome installation
google-chrome --version

# ChromeDriver will be managed by webdriver-manager in Python
# No manual ChromeDriver installation needed

echo "Chrome installation complete!"
echo "ChromeDriver will be automatically managed by webdriver-manager"
