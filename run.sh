#!/bin/bash

# DealNews Scraper Run Script

echo "Starting DealNews Scraper..."

# Create exports directory if it doesn't exist
mkdir -p exports

# Run the scraper
python run.py

echo "Scraping completed. Check exports/ directory for results."
