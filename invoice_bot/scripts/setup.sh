#!/bin/bash

echo "Setting up RPA Invoice Processing Bot environment..."

# 1. Create a Python virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate # On Windows, use `venv\Scripts\activate`

# 2. Install Python dependencies
echo "Installing Python dependencies from requirements.txt..."
pip install -r requirements.txt

# 3. Create necessary directories if they don't exist
echo "Creating necessary directories (sample_invoices, output, logs)..."
mkdir -p sample_invoices
mkdir -p output
mkdir -p logs

echo "Setup complete. To activate the virtual environment, run 'source venv/bin/activate'."
echo "To run the bot, navigate to the 'src' directory and execute 'python main.py'."
