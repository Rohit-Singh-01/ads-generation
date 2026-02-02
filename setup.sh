#!/bin/bash
# Streamlit Cloud setup script for Playwright
set -e

echo "======================================"
echo "Installing Playwright for Production"
echo "======================================"

# Install system dependencies first
echo "Installing system dependencies..."
apt-get update || true
apt-get install -y wget gnupg || true

# Install Playwright browsers
echo "Installing Playwright Chromium..."
playwright install chromium

# Install browser dependencies
echo "Installing Chromium dependencies..."
playwright install-deps chromium || true

# Verify installation
echo "Verifying Playwright installation..."
python -c "from playwright.sync_api import sync_playwright; print('✅ Playwright installed successfully')" || echo "⚠️ Playwright verification failed"

echo "======================================"
echo "Playwright setup complete!"
echo "======================================"
