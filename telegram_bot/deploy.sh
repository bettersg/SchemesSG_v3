#!/bin/bash

# Run this script from the telegram_bot folder

# Create virtual environment
echo "Creating virtual environment..."
python -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run the telegram bot
echo "Starting telegram bot..."
python app.py
