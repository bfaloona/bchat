#!/bin/bash
set -e

echo "Installing dependencies..."
pip install -e ".[development]"
echo "Dependencies installed successfully."
