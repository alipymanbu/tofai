#!/bin/bash

# Script to add all secrets from a .env file to GitHub repository secrets
# Usage: ./add_secrets_to_github.sh /path/to/.env-file repository-name

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "GitHub CLI (gh) is not installed. Please install it first."
    echo "See https://cli.github.com/ for installation instructions."
    exit 1
fi

# Check if user is authenticated with GitHub
if ! gh auth status &> /dev/null; then
    echo "You are not authenticated with GitHub. Please run 'gh auth login' first."
    exit 1
fi

# Check if arguments are provided
if [ "$#" -ne 2 ]; then
    echo "Usage: ./add_secrets_to_github.sh /path/to/.env-file repository-name"
    echo "Example: ./add_secrets_to_github.sh /Users/arjunsharma/Projects/tof-agent/.tofai-secrets.env tofai-co/tofai"
    exit 1
fi

ENV_FILE="$1"
REPO_NAME="$2"

# Check if env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo "Error: File $ENV_FILE does not exist."
    exit 1
fi

echo "Adding secrets from $ENV_FILE to GitHub repository $REPO_NAME..."

# Count how many secrets we're about to set
secret_count=0
valid_secrets=()
while IFS= read -r line || [[ -n "$line" ]]; do
    # Skip empty lines and comments
    if [[ -z "$line" || "$line" =~ ^\s*# ]]; then
        continue
    fi
    
    # Extract variable name and value
    if [[ "$line" =~ ^([^=]+)=(.*)$ ]]; then
        name="${BASH_REMATCH[1]}"
        value="${BASH_REMATCH[2]}"
        
        # Remove surrounding quotes if present
        value="${value#\"}"
        value="${value%\"}"
        value="${value#\'}"
        value="${value%\'}"
        
        # Skip empty values
        if [[ -z "$value" ]]; then
            echo "Warning: Empty value for $name, skipping"
            continue
        fi
        
        valid_secrets+=("$name")
        ((secret_count++))
    fi
done < "$ENV_FILE"

echo "Found $secret_count non-empty secrets to add."
echo "Secret names to be added: ${valid_secrets[*]}"
echo ""

read -p "Continue with adding these secrets? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Operation cancelled."
    exit 0
fi

# Now process the file again to actually add the secrets
while IFS= read -r line || [[ -n "$line" ]]; do
    # Skip empty lines and comments
    if [[ -z "$line" || "$line" =~ ^\s*# ]]; then
        continue
    fi
    
    # Extract variable name and value
    if [[ "$line" =~ ^([^=]+)=(.*)$ ]]; then
        name="${BASH_REMATCH[1]}"
        value="${BASH_REMATCH[2]}"
        
        # Remove surrounding quotes if present
        value="${value#\"}"
        value="${value%\"}"
        value="${value#\'}"
        value="${value%\'}"
        
        # Skip empty values
        if [[ -z "$value" ]]; then
            continue
        fi
        
        # Show partial value for verification (show only first 4 chars, or less if shorter)
        value_length=${#value}
        if [ $value_length -le 4 ]; then
            preview="${value}"
        else
            preview="${value:0:4}..."
        fi
        
        echo "Setting secret: $name (Value preview: $preview)"
        
        # Set the secret using GitHub CLI
        if ! gh secret set "$name" -b "$value" -R "$REPO_NAME"; then
            echo "  Failed to set secret $name"
        else
            echo "  Secret $name set successfully"
        fi
    else
        echo "Warning: Could not parse line: $line"
    fi
done < "$ENV_FILE"

echo "Completed adding secrets to GitHub repository $REPO_NAME"
