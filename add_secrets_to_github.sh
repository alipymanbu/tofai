#!/bin/bash

# Script to add all secrets from a .env or .yaml file to GitHub repository secrets
# Usage: ./add_secrets_to_github.sh /path/to/secrets-file repository-name

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
    echo "Usage: ./add_secrets_to_github.sh /path/to/secrets-file repository-name"
    echo "Supports both .env and .yaml/.yml files"
    echo "Example (env): ./add_secrets_to_github.sh /Users/arjunsharma/Projects/tof-agent/.tofai-secrets.env tofai-co/tofai"
    echo "Example (yaml): ./add_secrets_to_github.sh /Users/arjunsharma/Projects/tof-agent/.tofai-secrets.env.yaml tofai-co/tofai"
    exit 1
fi

SECRETS_FILE="$1"
REPO_NAME="$2"

# Check if secrets file exists
if [ ! -f "$SECRETS_FILE" ]; then
    echo "Error: File $SECRETS_FILE does not exist."
    exit 1
fi

# Determine file type based on extension
FILE_EXTENSION="${SECRETS_FILE##*.}"
if [[ "$FILE_EXTENSION" == "yaml" || "$FILE_EXTENSION" == "yml" ]]; then
    FILE_TYPE="yaml"
    echo "Detected YAML file format"
elif [[ "$FILE_EXTENSION" == "env" ]]; then
    FILE_TYPE="env"
    echo "Detected .env file format"
else
    # Try to detect based on content
    if head -5 "$SECRETS_FILE" | grep -q "^[A-Z_]*:" && ! head -5 "$SECRETS_FILE" | grep -q "="; then
        FILE_TYPE="yaml"
        echo "Auto-detected YAML file format based on content"
    else
        FILE_TYPE="env"
        echo "Auto-detected .env file format based on content"
    fi
fi

echo "Adding secrets from $SECRETS_FILE to GitHub repository $REPO_NAME..."

# Create temporary files to store secret names and values
TEMP_NAMES=$(mktemp)
TEMP_VALUES=$(mktemp)

# Cleanup function
cleanup() {
    rm -f "$TEMP_NAMES" "$TEMP_VALUES"
}
trap cleanup EXIT

# Function to parse files and store secrets in temporary files
parse_file() {
    local file="$1"
    local file_type="$2"
    local count=0
    
    > "$TEMP_NAMES"  # Clear temp files
    > "$TEMP_VALUES"
    
    if [[ "$file_type" == "yaml" ]]; then
        # Parse YAML format
        while IFS= read -r line || [[ -n "$line" ]]; do
            # Skip empty lines and comments
            if [[ -z "$line" || "$line" =~ ^\s*# ]]; then
                continue
            fi
            
            # Extract variable name and value from YAML format (KEY: "VALUE" or KEY: VALUE)
            if [[ "$line" =~ ^([^:]+):[[:space:]]*(.*)$ ]]; then
                name="${BASH_REMATCH[1]}"
                name="${name// /}"  # Remove spaces from name
                value="${BASH_REMATCH[2]}"
                
                # Remove surrounding quotes if present
                if [[ "$value" =~ ^\"(.*)\"$ ]]; then
                    value="${BASH_REMATCH[1]}"
                elif [[ "$value" =~ ^\'(.*)\'$ ]]; then
                    value="${BASH_REMATCH[1]}"
                elif [[ "$value" =~ ^\"(.*)$ ]]; then
                    # Handle unclosed quotes (common in YAML with multiline strings)
                    value="${BASH_REMATCH[1]}"
                elif [[ "$value" =~ ^\'(.*)$ ]]; then
                    # Handle unclosed quotes (common in YAML with multiline strings)
                    value="${BASH_REMATCH[1]}"
                fi
                
                # Skip empty values
                if [[ -n "$value" ]]; then
                    echo "$name" >> "$TEMP_NAMES"
                    echo "$value" >> "$TEMP_VALUES"
                    ((count++))
                else
                    echo "Warning: Empty value for $name, skipping"
                fi
            fi
        done < "$file"
    else
        # Parse .env format
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
                if [[ -n "$value" ]]; then
                    echo "$name" >> "$TEMP_NAMES"
                    echo "$value" >> "$TEMP_VALUES"
                    ((count++))
                else
                    echo "Warning: Empty value for $name, skipping"
                fi
            fi
        done < "$file"
    fi
    
    return $count
}

# Parse the file
parse_file "$SECRETS_FILE" "$FILE_TYPE"
secret_count=$?

# Read the secret names into an array (compatible with older bash)
valid_secrets=()
while IFS= read -r name; do
    valid_secrets+=("$name")
done < "$TEMP_NAMES"

echo "Found $secret_count non-empty secrets to add."
echo "Secret names to be added: ${valid_secrets[*]}"
echo ""

read -p "Continue with adding these secrets? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Operation cancelled."
    exit 0
fi

# Add the secrets to GitHub
i=0
while IFS= read -r name && IFS= read -r value <&3; do
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
    
    ((i++))
done < "$TEMP_NAMES" 3< "$TEMP_VALUES"

echo "Completed adding secrets to GitHub repository $REPO_NAME"