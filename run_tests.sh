#!/bin/bash
echo "Cleaning caches..."
find . -type d -name "__pycache__" -exec rm -rf {} +
rm -rf .pytest_cache
rm -rf htmlcov .coverage # Optional

echo "Running tests..."
pdm run pytest -s -v "$@"
