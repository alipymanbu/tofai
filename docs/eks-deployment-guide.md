# TOF.ai EKS Deployment Guide

This guide provides step-by-step instructions for deploying the TOF.ai backend on Amazon EKS.

## Prerequisites

- AWS CLI installed and configured
- eksctl installed
- kubectl installed
- Helm installed (for AWS Load Balancer Controller)
- Docker installed (for building and pushing container images)

## 1. Create EKS Cluster

Create an Amazon EKS cluster with a managed node group:

```bash
eksctl create cluster \
  --name tofai-cluster \
  --region us-east-1 \
  --version 1.27 \
  --nodegroup-name tofai-nodes \
  --node-type t3.medium \
  --nodes 2 \
  --nodes-min 1 \
  --nodes-max 3 \
  --managed
```

This process typically takes 15-20 minutes to complete.

## 2. Create Amazon ECR Repository

Create an ECR repository to store your Docker images:

```bash
aws ecr create-repository \
  --repository-name tofai-backend \
  --region us-east-1
```

## 3. Set Up S3 Buckets for Media Storage

Create the required S3 buckets for different media types:

```bash
# Create buckets
aws s3 mb s3://image-brand-awareness-video --region us-east-2
aws s3 mb s3://speech-brand-awareness-video --region us-east-2
aws s3 mb s3://music-brand-awareness-video --region us-east-2
aws s3 mb s3://video-brand-awareness-video --region us-east-2

# Configure CORS for each bucket
aws s3api put-bucket-cors --bucket image-brand-awareness-video --cors-configuration '{
  "CORSRules": [
    {
      "AllowedOrigins": ["*"],
      "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
      "AllowedHeaders": ["*"],
      "ExposeHeaders": ["ETag"]
    }
  ]
}'
```

Repeat the CORS configuration for the other buckets.

## 4. Create SSL Certificate with AWS Certificate Manager

Create and validate an SSL certificate for your API domain:

```bash
aws acm request-certificate \
  --domain-name api.tofai.com \
  --validation-method DNS \
  --region us-east-1
```

Follow the instructions in the AWS console to validate the certificate by adding the required DNS records.

## 5. Install AWS Load Balancer Controller

The AWS Load Balancer Controller is required for the ingress to work properly:

```bash
# Install the TargetGroupBinding CRDs
kubectl apply -k "github.com/aws/eks-charts/stable/aws-load-balancer-controller//crds?ref=master"

# Add the EKS chart repo
helm repo add eks https://aws.github.io/eks-charts

# Get your VPC ID
VPC_ID=$(aws eks describe-cluster --name tofai-cluster --query "cluster.resourcesVpcConfig.vpcId" --output text)

# Install the AWS Load Balancer Controller
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=tofai-cluster \
  --set serviceAccount.create=true \
  --set region=us-east-1 \
  --set vpcId=$VPC_ID
```

## 6. Set Up IAM Roles for Service Accounts (IRSA)

For proper AWS service integration, set up IRSA:

```bash
eksctl create iamserviceaccount \
  --name aws-load-balancer-controller \
  --namespace kube-system \
  --cluster tofai-cluster \
  --attach-policy-arn arn:aws:iam::aws:policy/AWSLoadBalancerControllerIAMPolicy \
  --approve
```

## 7. Build and Push Docker Image to ECR

Build your Docker image and push it to the ECR repository:

```bash
# Get the ECR repository URI
ECR_URI=$(aws ecr describe-repositories --repository-names tofai-backend --query "repositories[0].repositoryUri" --output text)

# Build the Docker image
docker build -t $ECR_URI:latest .

# Log in to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_URI

# Push the image
docker push $ECR_URI:latest
```

## 8. Generate Kubernetes Secrets

Run the script to generate the Kubernetes secrets file:

```bash
# Make the script executable
chmod +x ./scripts/generate-k8s-secrets.sh

# Set environment variables for your secrets
export MONGODB_URI="your_mongodb_uri"
export REDIS_HOST="your_redis_host"
export REDIS_PORT="your_redis_port"
export REDIS_USER="your_redis_user"
export REDIS_SECRET="your_redis_password"
# ... set all other required environment variables

# Generate the secrets file
./scripts/generate-k8s-secrets.sh
```

## 9. Deploy the Application

Apply the Kubernetes manifests to deploy your application:

```bash
# Apply the secrets first
kubectl apply -f k8s/secrets.yaml

# Replace placeholder values in deployment.yaml
IMAGE_TAG="latest"
sed -i "" "s|\${ECR_REPOSITORY_URI}|$ECR_URI|g" k8s/deployment.yaml
sed -i "" "s|\${IMAGE_TAG}|$IMAGE_TAG|g" k8s/deployment.yaml

# Replace placeholder values in ingress.yaml
CERTIFICATE_ARN=$(aws acm list-certificates --query "CertificateSummaryList[?DomainName=='api.tofai.com'].CertificateArn" --output text)
sed -i "" "s|\${CERTIFICATE_ARN}|$CERTIFICATE_ARN|g" k8s/ingress.yaml

# Apply the deployment, service, and ingress
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
```

## 10. Set Up DNS with Route 53

Create an A record in your Route 53 hosted zone pointing to the ALB:

1. Get the ALB hostname:
   ```bash
   kubectl get ingress tofai-backend-ingress -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
   ```

2. Create an A record in Route 53 for api.tofai.com pointing to the ALB (as an alias)

## 11. Set Up Monitoring

### Configure CloudWatch Container Insights

```bash
# Enable Container Insights
eksctl utils enable-container-insights \
  --cluster tofai-cluster \
  --region us-east-1

# Create a log group for the application
aws logs create-log-group --log-group-name /aws/eks/tofai/application --region us-east-1
```

## 12. Verify Deployment

Check that your deployment is running properly:

```bash
# Check pods
kubectl get pods

# Check services
kubectl get services

# Check ingress
kubectl get ingress

# Check logs
kubectl logs -l app=tofai-backend
```

## 13. Additional Security Measures

### Set Up Network Policies

Create a basic network policy:

```bash
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: tofai-network-policy
  namespace: default
spec:
  podSelector:
    matchLabels:
      app: tofai-backend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: tofai-backend
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - {}
EOF
```

## Troubleshooting

- **Cluster Creation Issues**: Run `eksctl utils describe-stacks --region=us-east-1 --cluster=tofai-cluster` to check the CloudFormation stack status
- **Pod Startup Issues**: Use `kubectl describe pod <pod-name>` to see detailed information about pod status
- **Ingress Issues**: Check the AWS Load Balancer Controller logs with `kubectl logs -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller`

## Cleanup (When Needed)

To delete the cluster and associated resources:

```bash
# Delete the cluster
eksctl delete cluster --name tofai-cluster --region us-east-1

# Delete ECR repository (optional)
aws ecr delete-repository --repository-name tofai-backend --force --region us-east-1

# Delete S3 buckets (optional)
aws s3 rb s3://image-brand-awareness-video --force
aws s3 rb s3://speech-brand-awareness-video --force
aws s3 rb s3://music-brand-awareness-video --force
aws s3 rb s3://video-brand-awareness-video --force
```

## Maintenance

- **Scaling**: Adjust node count with `eksctl scale nodegroup --cluster=tofai-cluster --nodes=<count> --name=tofai-nodes`
- **Updates**: Update cluster version with `eksctl update cluster --name=tofai-cluster --approve`
- **Monitoring**: Set up CloudWatch dashboards and alarms for critical metrics
