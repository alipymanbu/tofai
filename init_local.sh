#!/bin/bash

# Make the script exit on error
set -e

echo "Initializing TOF.ai local development environment..."

# Check if Docker is installed
# if ! command -v docker &> /dev/null; then
#     echo "Docker is required but not installed. Please install Docker and try again."
#     exit 1
# fi

# # Check if Docker Compose is installed
# if ! command -v docker-compose &> /dev/null; then
#     echo "Docker Compose is required but not installed. Please install Docker Compose and try again."
#     exit 1
# fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed. Please install Python 3 and try again."
    exit 1
fi

# Create a virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate the virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# # Start MongoDB and Redis with Docker Compose
# echo "Starting MongoDB and Redis..."
# docker-compose up -d mongo redis

# Create .env file if it doesn't exist
# if [ ! -f ".env" ]; then
#     echo "Creating default .env file..."
#     cat > .env << EOL
# # Server
# PORT=8000
# DEBUG=True
# ENVIRONMENT=development

# # Database
# MONGODB_URI=mongodb://localhost:27017
# DATABASE_NAME=tofai

# # Redis
# REDIS_URI=redis://localhost:6379/0

# # AI Services
# CLAUDE_API_KEY=your_claude_api_key
# OPENAI_API_KEY=your_openai_api_key

# # Celery settings
# CELERY_BROKER_URL=redis://localhost:6379/1
# CELERY_RESULT_BACKEND=redis://localhost:6379/1

# # Storage
# S3_BUCKET=tofai-media
# S3_REGION=us-east-1
# AWS_ACCESS_KEY_ID=your_aws_access_key
# AWS_SECRET_ACCESS_KEY=your_aws_secret_key
# EOL
#     echo "Please update the .env file with your actual API keys and credentials."
# fi

# Make the script executable
chmod +x init_local.sh

echo "Starting the FastAPI application..."
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
API_PID=$!

# echo "Starting Celery worker..."
# celery -A api.celery_worker worker --loglevel=info &
# CELERY_PID=$!

echo "====================================================="
echo "TOF.ai local environment is now running!"
echo "API is available at: http://localhost:8000"
echo "API documentation: http://localhost:8000/docs"
echo "====================================================="
echo "Press Ctrl+C to stop all services"

# Trap for graceful shutdown
trap "kill $API_PID; echo 'TOF.ai services stopped'; exit 0" INT TERM

# Keep the script running
wait
