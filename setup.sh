#!/bin/bash

echo "Installing TOM Toolkit..."
pip install tomtoolkit

echo "Installing additional dependencies..."
pip install -r requirements.txt

echo "Setup complete!"