#!/bin/bash

# This script creates a .env file from the .env.template file
# It's meant to be run once when setting up the project

set -e

ENV_TEMPLATE=".env.template"
ENV_FILE=".tofai-secrets.env"

# Check if .env file already exists
if [ -f "$ENV_FILE" ]; then
    read -p "A .env file already exists. Do you want to overwrite it? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Operation cancelled."
        exit 0
    fi
fi

# Copy the template file
cp "$ENV_TEMPLATE" "$ENV_FILE"

# Set proper permissions (readable only by the user)
chmod 600 "$ENV_FILE"

echo "Created .env file from template."
echo "IMPORTANT: Update the .env file with your actual secrets before running the application."
echo "The .env file has been set to be readable only by you for security."
