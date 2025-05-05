#!/bin/bash

# This script generates a Kubernetes secrets file based on environment variables
# Run this before deploying to EKS to create the secrets.yaml file

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"

cat > "$PROJECT_ROOT/k8s/secrets.yaml" << EOL
apiVersion: v1
kind: Secret
metadata:
  name: tofai-secrets
type: Opaque
data:
  MONGODB_URI: $(echo -n "${MONGODB_URI}" | base64 -w 0)
  REDIS_HOST: $(echo -n "${REDIS_HOST}" | base64 -w 0)
  REDIS_PORT: $(echo -n "${REDIS_PORT}" | base64 -w 0)
  REDIS_USER: $(echo -n "${REDIS_USER}" | base64 -w 0)
  REDIS_SECRET: $(echo -n "${REDIS_SECRET}" | base64 -w 0)
  CLAUDE_API_KEY: $(echo -n "${CLAUDE_API_KEY}" | base64 -w 0)
  OPENAI_API_KEY: $(echo -n "${OPENAI_API_KEY}" | base64 -w 0)
  GEMINI_API_PROJECT_NUMBER: $(echo -n "${GEMINI_API_PROJECT_NUMBER}" | base64 -w 0)
  GEMINI_API_SECRET: $(echo -n "${GEMINI_API_SECRET}" | base64 -w 0)
  ELEVEN_TTS_SECRET: $(echo -n "${ELEVEN_TTS_SECRET}" | base64 -w 0)
  GOOGLE_SEARCH_API_KEY: $(echo -n "${GOOGLE_SEARCH_API_KEY}" | base64 -w 0)
  GOOGLE_CSE_ID: $(echo -n "${GOOGLE_CSE_ID}" | base64 -w 0)
  AWS_ACCESS_KEY_ID: $(echo -n "${AWS_ACCESS_KEY_ID}" | base64 -w 0)
  AWS_SECRET_ACCESS_KEY: $(echo -n "${AWS_SECRET_ACCESS_KEY}" | base64 -w 0)
  AWS_REGION: $(echo -n "${AWS_REGION}" | base64 -w 0)
  S3_BUCKET: $(echo -n "${S3_BUCKET}" | base64 -w 0)
  S3_REGION: $(echo -n "${S3_REGION}" | base64 -w 0)
  SECRET_KEY: $(echo -n "${SECRET_KEY}" | base64 -w 0)
  COGNITO_REGION: $(echo -n "${COGNITO_REGION}" | base64 -w 0)
  COGNITO_USER_POOL_ID: $(echo -n "${COGNITO_USER_POOL_ID}" | base64 -w 0)
  COGNITO_CLIENT_ID: $(echo -n "${COGNITO_CLIENT_ID}" | base64 -w 0)
  COGNITO_CLIENT_SECRET: $(echo -n "${COGNITO_CLIENT_SECRET}" | base64 -w 0)
  COGNITO_DOMAIN: $(echo -n "${COGNITO_DOMAIN}" | base64 -w 0)
  COGNITO_REDIRECT_URL: $(echo -n "${COGNITO_REDIRECT_URL}" | base64 -w 0)
  COGNITO_LOGOUT_URL: $(echo -n "${COGNITO_LOGOUT_URL}" | base64 -w 0)
  COGNITO_SCOPE: $(echo -n "${COGNITO_SCOPE}" | base64 -w 0)
  COGNITO_TOKEN_SIGNING_URL: $(echo -n "${COGNITO_TOKEN_SIGNING_URL}" | base64 -w 0)
EOL

echo "Generated k8s/secrets.yaml with encoded secrets"
