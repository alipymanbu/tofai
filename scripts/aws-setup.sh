#!/bin/bash
# Setup script for AWS EKS deployment prerequisites

set -e

echo "Setting up AWS EKS deployment prerequisites..."

# Check for required tools
echo "Checking for required tools..."

if ! command -v aws &> /dev/null; then
    echo "AWS CLI not found. Please install it first:"
    echo "brew install awscli"
    exit 1
fi

if ! command -v eksctl &> /dev/null; then
    echo "eksctl not found. Please install it first:"
    echo "brew install eksctl"
    exit 1
fi

if ! command -v kubectl &> /dev/null; then
    echo "kubectl not found. Please install it first:"
    echo "brew install kubectl"
    exit 1
fi

if ! command -v helm &> /dev/null; then
    echo "Helm not found. Please install it first:"
    echo "brew install helm"
    exit 1
fi

# Check AWS credentials
echo "Checking AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo "AWS credentials not configured or invalid."
    echo "Please run 'aws configure' to set up your credentials."
    exit 1
fi

echo "AWS credentials are valid."

# Set variables
read -p "Enter your desired AWS region (default: us-east-1): " AWS_REGION
AWS_REGION=${AWS_REGION:-us-east-1}

read -p "Enter your cluster name (default: tofai-cluster): " CLUSTER_NAME
CLUSTER_NAME=${CLUSTER_NAME:-tofai-cluster}

read -p "Enter your API domain name (default: api.tofai.com): " API_DOMAIN
API_DOMAIN=${API_DOMAIN:-api.tofai.com}

# Create ECR repository
echo "Creating ECR repository..."
aws ecr create-repository --repository-name tofai-backend --region $AWS_REGION || echo "Repository may already exist, continuing..."

# Create S3 buckets
echo "Creating S3 buckets..."
aws s3 mb s3://image-brand-awareness-video --region $AWS_REGION || echo "Bucket may already exist, continuing..."
aws s3 mb s3://speech-brand-awareness-video --region $AWS_REGION || echo "Bucket may already exist, continuing..."
aws s3 mb s3://music-brand-awareness-video --region $AWS_REGION || echo "Bucket may already exist, continuing..."
aws s3 mb s3://video-brand-awareness-video --region $AWS_REGION || echo "Bucket may already exist, continuing..."

# Configure CORS for each bucket
echo "Configuring CORS for S3 buckets..."
CORS_CONFIG='{
  "CORSRules": [
    {
      "AllowedOrigins": ["*"],
      "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
      "AllowedHeaders": ["*"],
      "ExposeHeaders": ["ETag"]
    }
  ]
}'

aws s3api put-bucket-cors --bucket image-brand-awareness-video --cors-configuration "$CORS_CONFIG" --region $AWS_REGION
aws s3api put-bucket-cors --bucket speech-brand-awareness-video --cors-configuration "$CORS_CONFIG" --region $AWS_REGION
aws s3api put-bucket-cors --bucket music-brand-awareness-video --cors-configuration "$CORS_CONFIG" --region $AWS_REGION
aws s3api put-bucket-cors --bucket video-brand-awareness-video --cors-configuration "$CORS_CONFIG" --region $AWS_REGION

# Request SSL certificate
echo "Requesting SSL certificate for $API_DOMAIN..."
aws acm request-certificate \
  --domain-name $API_DOMAIN \
  --validation-method DNS \
  --region $AWS_REGION

echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Follow the instructions in ACM to validate your certificate"
echo "2. Create your EKS cluster with: "
echo "   eksctl create cluster \\"
echo "     --name $CLUSTER_NAME \\"
echo "     --region $AWS_REGION \\"
echo "     --version 1.27 \\"
echo "     --nodegroup-name tofai-nodes \\"
echo "     --node-type t3.medium \\"
echo "     --nodes 2 \\"
echo "     --nodes-min 1 \\"
echo "     --nodes-max 3 \\"
echo "     --managed"
echo ""
echo "For more details, see the full deployment guide in docs/eks-deployment-guide.md"
