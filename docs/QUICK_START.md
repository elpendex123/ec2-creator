# EC2 Provisioner — Quick Start Guide

Get up and running with the EC2 provisioner in 5 minutes.

## Prerequisites

- Python 3.11+
- AWS credentials configured locally
- Terraform installed (for Terraform backend)
- Docker & Docker Compose (optional, for containerized deployment)

## Local Setup (Stage 1)

### 1. Install Dependencies

```bash
cd ~/PROJECT/ec2-creator
python3 -m pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the project root:

```bash
# AWS Credentials
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1

# SMTP Email Notifications
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your.email@gmail.com
SMTP_PASSWORD=your_app_password
NOTIFICATION_EMAIL=your.email@gmail.com

# App Configuration
BACKEND=awscli                    # or 'terraform'
DB_PATH=./data/instances.db

# ECR/EKS (for later stages)
ECR_REPO=
ECR_IMAGE_TAG=latest
EKS_CLUSTER_NAME=
```

### 3. Start the FastAPI App

```bash
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

App is now running at `http://localhost:8000`

### 4. Access the API

**Swagger UI (Interactive Docs):**
```
http://localhost:8000/docs
```

**Create an instance:**
```bash
curl -X POST http://localhost:8000/instances \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-server",
    "ami": "ami-026992d753d5622bc",
    "instance_type": "t3.micro",
    "storage_gb": 8
  }'
```

**List instances:**
```bash
curl http://localhost:8000/instances
```

**Get instance details:**
```bash
curl http://localhost:8000/instances/i-1234567890abcdef0
```

**Start instance:**
```bash
curl -X POST http://localhost:8000/instances/i-1234567890abcdef0/start
```

**Stop instance:**
```bash
curl -X POST http://localhost:8000/instances/i-1234567890abcdef0/stop
```

**Destroy instance:**
```bash
curl -X DELETE http://localhost:8000/instances/i-1234567890abcdef0
```

## Free-Tier Configuration

### Allowed Instance Types
- `t3.micro` ✓
- `t4g.micro` ✓

### Free-Tier AMIs by Region

**us-east-1:**
- `ami-0c02fb55956c7d316` - Amazon Linux 2 (older)
- `ami-026992d753d5622bc` - Amazon Linux 2 (current)
- `ami-026ebee89baf5eb77` - Ubuntu 20.04 LTS

**us-east-2:**
- `ami-0ea3c35d6814e3cb6`
- `ami-0229d9f8ca82508cc`

**us-west-1:**
- `ami-0fb653ca2d3203ac1`
- `ami-0f4c5fd4dd4dd1051`

**us-west-2:**
- `ami-0430580de6244e02b`
- `ami-0e472933a1666f130`

**eu-west-1:**
- `ami-0d3d0c0e87e3a77fd`
- `ami-0f1a8f29ed2ad83e2`

## SSH Access

Once an instance is created:

```bash
ssh -i ~/.ssh/my_ec2_keypair.pem ec2-user@<public_ip>
```

The key pair name is: `my_ec2_keypair`

## Backend Selection

Choose your provisioning backend per request:

**AWS CLI (default):**
```bash
curl -X POST "http://localhost:8000/instances?backend=awscli" ...
```

**Terraform:**
```bash
curl -X POST "http://localhost:8000/instances?backend=terraform" ...
```

## Email Notifications

The API sends automated emails for:
- Instance creation
- Instance start
- Instance stop
- Instance destruction

Emails are sent to the address in `NOTIFICATION_EMAIL` via `SMTP_USER`.

## Next Steps

- See [SSH_SETUP.md](SSH_SETUP.md) for key pair configuration details
- See [API_REFERENCE.md](API_REFERENCE.md) for full endpoint documentation
- See [DEPLOYMENT.md](DEPLOYMENT.md) for Stages 2-4 (Docker, Minikube, EKS)
