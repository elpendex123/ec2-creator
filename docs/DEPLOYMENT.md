# EC2 Provisioner — Deployment Stages

Deploy the EC2 provisioner across 4 stages: local Linux → Docker → Minikube → EKS.

## Stage 1: Local Linux (Development)

Deploy directly on Linux with native tooling.

### Prerequisites

- Linux system (Ubuntu 20.04+)
- Python 3.11+
- Terraform 1.0+
- AWS CLI v2
- Bash shell

### Setup

```bash
cd ~/PROJECTS/ec2-creator

# Install dependencies
python3 -m pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your AWS credentials and SMTP settings

# Ensure scripts are executable
chmod +x aws_cli_bash_scripts/*.sh
chmod +x terraform_bash_scripts/*.sh
```

### Run

```bash
# Start FastAPI
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, test
curl http://localhost:8000/health
```

### Jenkins Pipeline

**File:** `jenkins/deployment/Jenkinsfile.local`

```groovy
stages:
  - Checkout
  - Lint (flake8)
  - Test (pytest)
  - Start (uvicorn)
```

### Verification

```bash
# Health check
curl http://localhost:8000/health

# Create test instance
curl -X POST http://localhost:8000/instances \
  -H "Content-Type: application/json" \
  -d '{"name":"test","ami":"ami-026992d753d5622bc","instance_type":"t3.micro","storage_gb":8}'

# List instances
curl http://localhost:8000/instances
```

---

## Stage 2: Docker (Local + ECR Push)

Containerize the app and push to Amazon ECR.

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- AWS CLI v2 configured
- ECR repository created in AWS

### Setup

```bash
# Create ECR repository (one time)
aws ecr create-repository --repository-name ec2-provisioner --region us-east-1

# Get ECR login info
aws ecr describe-repositories --repository-names ec2-provisioner \
  --query 'repositories[0].repositoryUri' --output text
# Output: 123456789.dkr.ecr.us-east-1.amazonaws.com/ec2-provisioner

# Update .env
ECR_REPO=123456789.dkr.ecr.us-east-1.amazonaws.com/ec2-provisioner
ECR_IMAGE_TAG=latest
```

### Build Image

```bash
# Build Docker image
docker build -t ec2-provisioner:latest -f Dockerfile .

# Tag for ECR
docker tag ec2-provisioner:latest \
  123456789.dkr.ecr.us-east-1.amazonaws.com/ec2-provisioner:latest
```

### Run Locally

```bash
# Start with Docker Compose
docker-compose up -d

# Verify
curl http://localhost:8000/health

# View logs
docker-compose logs -f api

# Stop
docker-compose down
```

### Push to ECR

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  123456789.dkr.ecr.us-east-1.amazonaws.com

# Push image
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/ec2-provisioner:latest

# Verify push
aws ecr describe-images --repository-name ec2-provisioner
```

### Jenkins Pipeline

**File:** `jenkins/deployment/Jenkinsfile.docker`

```groovy
stages:
  - Checkout
  - Lint (flake8)
  - Test (pytest)
  - Docker Build
  - Docker Compose Up
  - ECR Login
  - Tag Image
  - Push to ECR
```

### Verification

```bash
# Verify image in ECR
aws ecr describe-images --repository-name ec2-provisioner \
  --query 'imageDetails[0]'
```

---

## Stage 3: Minikube (Local Kubernetes)

Deploy to local Kubernetes cluster via Minikube.

### Prerequisites

- Minikube 1.25+ installed and running
- kubectl configured
- Docker or Hyperkit as driver
- Image already pushed to ECR (Stage 2)

### Setup

```bash
# Start Minikube
minikube start --driver=docker --cpus=4 --memory=4096

# Verify it's running
kubectl cluster-info

# Create namespace
kubectl create namespace ec2-provisioner

# Create ECR pull secret
kubectl create secret docker-registry ecr-secret \
  --docker-server=123456789.dkr.ecr.us-east-1.amazonaws.com \
  --docker-username=AWS \
  --docker-password=$(aws ecr get-login-password --region us-east-1) \
  --docker-email=user@example.com \
  -n ec2-provisioner
```

### Deploy

```bash
# Update image URI in k8s/deployment.yaml
# FROM: image: 123456789.dkr.ecr.us-east-1.amazonaws.com/ec2-provisioner:latest

# Apply manifests
kubectl apply -f k8s/deployment.yaml -n ec2-provisioner
kubectl apply -f k8s/service.yaml -n ec2-provisioner
kubectl apply -f k8s/configmap.yaml -n ec2-provisioner
```

### Access

```bash
# Get service port (minikube uses NodePort)
kubectl get svc -n ec2-provisioner
# OUTPUT: ec2-provisioner   NodePort    10.96.100.200   <none>   8000:31234/TCP

# Minikube URL
minikube service ec2-provisioner -n ec2-provisioner --url
# OUTPUT: http://192.168.49.2:31234

# Test
curl http://192.168.49.2:31234/health
```

### Jenkins Pipeline

**File:** `jenkins/deployment/Jenkinsfile.minikube`

```groovy
stages:
  - Checkout
  - ECR Login
  - Configure Minikube ECR Secret
  - kubectl Apply
  - Verify Pods Running
```

### Verification

```bash
# Check pods
kubectl get pods -n ec2-provisioner

# Check service
kubectl get svc -n ec2-provisioner

# View logs
kubectl logs -f deployment/ec2-provisioner -n ec2-provisioner

# Port forward for testing
kubectl port-forward -n ec2-provisioner svc/ec2-provisioner 8000:8000

# In another terminal
curl http://localhost:8000/health
```

### Cleanup

```bash
kubectl delete namespace ec2-provisioner
```

---

## Stage 4: EKS (Production Kubernetes)

Deploy to Amazon EKS (production Kubernetes cluster).

### Prerequisites

- AWS account with EKS permissions
- kubectl configured
- Terraform 1.0+
- ECR image already pushed (Stage 2)

### Create EKS Cluster

```bash
# Initialize Terraform
cd terraform/eks
terraform init

# Apply EKS infrastructure
terraform apply

# Get kubeconfig
aws eks update-kubeconfig --name ec2-provisioner-cluster --region us-east-1

# Verify connection
kubectl cluster-info
```

### Setup ECR Access

```bash
# Create ECR pull secret in EKS
kubectl create secret docker-registry ecr-secret \
  --docker-server=123456789.dkr.ecr.us-east-1.amazonaws.com \
  --docker-username=AWS \
  --docker-password=$(aws ecr get-login-password --region us-east-1) \
  --docker-email=user@example.com \
  -n ec2-provisioner
```

### Deploy

```bash
# Apply manifests to EKS
kubectl apply -f k8s/deployment.yaml -n ec2-provisioner
kubectl apply -f k8s/service.yaml -n ec2-provisioner
kubectl apply -f k8s/configmap.yaml -n ec2-provisioner
```

### Access

```bash
# Get LoadBalancer URL (EKS uses AWS ALB)
kubectl get svc -n ec2-provisioner
# OUTPUT: ec2-provisioner   LoadBalancer   10.0.100.200   a1234567-1234567.us-east-1.elb.amazonaws.com   8000:31234/TCP

# Test
curl http://a1234567-1234567.us-east-1.elb.amazonaws.com:8000/health
```

### Jenkins Pipeline

**File:** `jenkins/deployment/Jenkinsfile.eks`

```groovy
stages:
  - Checkout
  - Terraform Init (eks/)
  - Terraform Apply (eks/)
  - Update Kubeconfig
  - kubectl Apply
  - Verify Deployment
```

### Verification

```bash
# Check deployment
kubectl get deployment -n ec2-provisioner

# Check pods
kubectl get pods -n ec2-provisioner

# Check service
kubectl get svc -n ec2-provisioner

# View logs
kubectl logs -f deployment/ec2-provisioner -n ec2-provisioner

# Port forward for testing
kubectl port-forward -n ec2-provisioner svc/ec2-provisioner 8000:8000
```

### Scaling

```bash
# Scale replicas
kubectl scale deployment ec2-provisioner --replicas=3 -n ec2-provisioner

# Auto-scaling (requires metrics-server)
kubectl autoscale deployment ec2-provisioner --min=2 --max=5 \
  --cpu-percent=50 -n ec2-provisioner
```

### Cleanup

```bash
# Delete Kubernetes resources
kubectl delete namespace ec2-provisioner

# Destroy EKS cluster
cd terraform/eks
terraform destroy -auto-approve
```

---

## Environment Variables by Stage

| Variable | Stage 1 | Stage 2 | Stage 3 | Stage 4 |
|----------|---------|---------|---------|---------|
| `BACKEND` | ✓ | ✓ | ✓ | ✓ |
| `AWS_ACCESS_KEY_ID` | ✓ | ✓ | ✓ | ✓ |
| `AWS_SECRET_ACCESS_KEY` | ✓ | ✓ | ✓ | ✓ |
| `SMTP_HOST` | ✓ | ✓ | ✓ | ✓ |
| `SMTP_PORT` | ✓ | ✓ | ✓ | ✓ |
| `SMTP_USER` | ✓ | ✓ | ✓ | ✓ |
| `SMTP_PASSWORD` | ✓ | ✓ | ✓ | ✓ |
| `NOTIFICATION_EMAIL` | ✓ | ✓ | ✓ | ✓ |
| `ECR_REPO` | — | ✓ | ✓ | ✓ |
| `ECR_IMAGE_TAG` | — | ✓ | ✓ | ✓ |
| `EKS_CLUSTER_NAME` | — | — | — | ✓ |

---

## Troubleshooting

### Stage 1: Local
- Check Python version: `python3 --version` (must be 3.11+)
- Check AWS credentials: `aws sts get-caller-identity`
- Check Terraform: `terraform -v`

### Stage 2: Docker
- Docker daemon running: `docker ps`
- ECR repository exists: `aws ecr describe-repositories`
- Credentials valid: `aws ecr get-login-password`

### Stage 3: Minikube
- Minikube running: `minikube status`
- kubectl context: `kubectl config current-context`
- Namespace created: `kubectl get ns ec2-provisioner`
- ECR secret created: `kubectl get secrets -n ec2-provisioner`

### Stage 4: EKS
- Cluster exists: `aws eks describe-cluster --name ec2-provisioner-cluster`
- kubeconfig updated: `kubectl cluster-info`
- Nodes ready: `kubectl get nodes`
- Pods running: `kubectl get pods -n ec2-provisioner`
