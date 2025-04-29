#!/bin/bash

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Install or update dependencies
echo "Installing dependencies..."
uv pip install -r requirements.txt

# Run the Streamlit app
echo "Starting the Browser Automation UI..."
streamlit run app.py 