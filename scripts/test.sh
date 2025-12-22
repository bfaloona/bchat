#!/bin/bash
set -e

echo "Running tests..."
pytest -v --no-header --tb=short
echo "Tests completed successfully."
