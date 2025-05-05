#!/bin/bash

# Script to delete all secrets from a GitHub repository
# Usage: ./delete_github_secrets.sh repository-name

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

# Check if repository name is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: ./delete_github_secrets.sh repository-name"
    echo "Example: ./delete_github_secrets.sh tofai-co/tofai"
    exit 1
fi

REPO_NAME="$1"

echo "Fetching secrets from GitHub repository $REPO_NAME..."
SECRETS=$(gh secret list -R "$REPO_NAME" --json name --jq '.[].name')

if [ -z "$SECRETS" ]; then
    echo "No secrets found in repository $REPO_NAME."
    exit 0
fi

echo "The following secrets will be deleted from $REPO_NAME:"
echo "$SECRETS"
echo ""

read -p "Are you sure you want to delete all these secrets? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Operation cancelled."
    exit 0
fi

echo "Deleting secrets from GitHub repository $REPO_NAME..."

for secret in $SECRETS; do
    echo "Deleting secret: $secret"
    if ! gh secret delete "$secret" -R "$REPO_NAME" 2>/dev/null; then
        echo "  Failed to delete secret $secret"
    else
        echo "  Secret $secret deleted successfully"
    fi
done

echo "Completed deleting secrets from GitHub repository $REPO_NAME"
