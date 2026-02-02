#!/bin/bash
# Streamlit Cloud setup script
# This runs after pip install but before the app starts

echo "Installing Playwright browsers..."
playwright install chromium
playwright install-deps chromium

echo "Playwright setup complete!"
