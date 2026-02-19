# EC2 Provisioner API

A FastAPI REST API for provisioning and managing AWS EC2 instances with dual backend support (Terraform and AWS CLI).

## Overview

**EC2 Provisioner** is a production-ready microservice that:
- ✅ Provisions EC2 instances with AWS CLI or Terraform
- ✅ Enforces free-tier constraints (t3.micro, t4g.micro only)
- ✅ Manages instance lifecycle (create, start, stop, destroy)
- ✅ Stores instance records in SQLite
- ✅ Sends email notifications on lifecycle events
- ✅ Deploys across 4 stages: Local → Docker → Minikube → EKS
- ✅ Includes Swagger/OpenAPI documentation

## Quick Start

```bash
# Install dependencies
python3 -m pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your AWS credentials and email settings

# Start the API
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Access Swagger UI
open http://localhost:8000/docs
```

## Documentation

All documentation is in the `docs/` directory:

| Document | Purpose |
|----------|---------|
| **[QUICK_START.md](docs/QUICK_START.md)** | Get up and running in 5 minutes |
| **[API_REFERENCE.md](docs/API_REFERENCE.md)** | Complete endpoint documentation |
| **[SSH_SETUP.md](docs/SSH_SETUP.md)** | Configure SSH key pairs for instance access |
| **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** | Deploy across 4 stages (Local, Docker, Minikube, EKS) |

## Tech Stack

### Backend
- **Language:** Python 3.11+
- **Framework:** FastAPI + Uvicorn
- **Infrastructure:** AWS (EC2, ECR, EKS)
- **Provisioning:** Terraform + AWS CLI (dual backend)
- **Persistence:** SQLite
- **Notifications:** SMTP (Gmail)
- **Container:** Docker + Docker Compose
- **K8s:** Minikube + Amazon EKS

### CI/CD
- **Jenkins** — Pipeline orchestration
- **GitHub Actions** — (optional) Alternative CI

## Free-Tier Configuration

### Allowed Instance Types
- `t3.micro` ✓
- `t4g.micro` ✓

### Allowed AMIs by Region

**us-east-1:**
- `ami-0c02fb55956c7d316` — Amazon Linux 2 (older)
- `ami-026992d753d5622bc` — Amazon Linux 2 (current)
- `ami-026ebee89baf5eb77` — Ubuntu 20.04 LTS

**us-east-2, us-west-1, us-west-2, eu-west-1:**
- See [QUICK_START.md](docs/QUICK_START.md) for region-specific AMIs

## Core Features

### 1. Instance Management

Create, list, start, stop, and destroy EC2 instances:

```bash
# Create
curl -X POST http://localhost:8000/instances \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-server",
    "ami": "ami-026992d753d5622bc",
    "instance_type": "t3.micro",
    "storage_gb": 8
  }'

# List
curl http://localhost:8000/instances

# Start/Stop
curl -X POST http://localhost:8000/instances/i-xxxxx/start
curl -X POST http://localhost:8000/instances/i-xxxxx/stop

# Destroy
curl -X DELETE http://localhost:8000/instances/i-xxxxx
```

### 2. Dual Backend Support

Choose provisioning engine per request:

```bash
# AWS CLI (default)
curl -X POST "http://localhost:8000/instances?backend=awscli" ...

# Terraform
curl -X POST "http://localhost:8000/instances?backend=terraform" ...
```

### 3. SSH Access

Instances are created with the `my_ec2_keypair` SSH key:

```bash
ssh -i ~/.ssh/my_ec2_keypair.pem ec2-user@<public_ip>
```

See [SSH_SETUP.md](docs/SSH_SETUP.md) for detailed setup instructions.

### 4. Email Notifications

Automated emails sent on:
- Instance creation ✉️
- Instance start ✉️
- Instance stop ✉️
- Instance destruction ✉️

Configure in `.env`:
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your.email@gmail.com
SMTP_PASSWORD=your_app_password
NOTIFICATION_EMAIL=recipient@example.com
```

### 5. API Documentation

Interactive Swagger UI at:
```
http://localhost:8000/docs
```

Alternative ReDoc:
```
http://localhost:8000/redoc
```

## Project Structure

```
ec2-provisioner/
├── app/                          # FastAPI application
│   ├── main.py                   # App entry point
│   ├── config.py                 # Settings & free-tier validation
│   ├── routers/
│   │   └── instances.py          # All endpoints
│   ├── services/
│   │   ├── terraform.py          # Terraform backend
│   │   ├── aws_cli.py            # AWS CLI backend
│   │   ├── db.py                 # SQLite ORM
│   │   └── notifications.py      # Email service
│   └── models/
│       └── instance.py           # Pydantic request/response models
├── terraform/
│   ├── ec2/                      # EC2 instance Terraform
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── eks/                      # EKS cluster Terraform
├── aws_cli_bash_scripts/         # AWS CLI wrapper scripts
│   ├── create_instance.sh
│   ├── list_instances.sh
│   ├── start_instance.sh
│   ├── stop_instance.sh
│   └── destroy_instance.sh
├── terraform_bash_scripts/       # Terraform wrapper scripts
│   ├── tf_init.sh
│   ├── tf_create.sh
│   ├── tf_list.sh
│   ├── tf_start.sh
│   ├── tf_stop.sh
│   └── tf_destroy.sh
├── jenkins/                      # CI/CD pipelines
│   ├── deployment/
│   │   ├── Jenkinsfile.local     # Stage 1
│   │   ├── Jenkinsfile.docker    # Stage 2
│   │   ├── Jenkinsfile.minikube  # Stage 3
│   │   └── Jenkinsfile.eks       # Stage 4
│   ├── terraform_jobs/           # Terraform EC2 operations
│   └── aws_cli_jobs/             # AWS CLI EC2 operations
├── k8s/                          # Kubernetes manifests
│   ├── deployment.yaml
│   ├── service.yaml
│   └── configmap.yaml
├── docs/                         # Documentation
│   ├── QUICK_START.md
│   ├── API_REFERENCE.md
│   ├── SSH_SETUP.md
│   └── DEPLOYMENT.md
├── Dockerfile                    # Container image
├── docker-compose.yml            # Local compose setup
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment template
└── README.md                     # This file
```

## Environment Variables

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
NOTIFICATION_EMAIL=recipient@example.com

# App Configuration
BACKEND=awscli                    # Default backend (awscli or terraform)
DB_PATH=./data/instances.db      # SQLite database location

# ECR / EKS (for Stage 2+ deployments)
ECR_REPO=
ECR_IMAGE_TAG=latest
EKS_CLUSTER_NAME=
```

## Free-Tier Validation

The API enforces AWS free-tier constraints:

✅ **Allowed:**
- Instance types: `t3.micro`, `t4g.micro`
- Whitelisted AMIs per region
- Storage: Any size >= 1 GB

❌ **Rejected:**
- Instance type: `t2.micro`, `t2.small`, etc.
- Non-whitelisted AMIs
- Invalid regions

Error response:
```json
{
  "detail": "Instance type 't2.large' or AMI 'ami-xxxxx' not allowed. Only t3.micro and t4g.micro instance types are free tier eligible."
}
```

## Deployment Stages

| Stage | Environment | Tooling | Purpose |
|-------|-------------|---------|---------|
| **1** | Local Linux | Python, Bash | Development & testing |
| **2** | Docker | Docker Compose, ECR | Containerization & registry |
| **3** | Minikube | kubectl, Minikube | Local Kubernetes testing |
| **4** | EKS | AWS, Terraform, kubectl | Production Kubernetes |

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed stage-by-stage instructions.

## Development

### Local Testing

```bash
# Install dev dependencies
python3 -m pip install -r requirements.txt

# Run tests
pytest tests/

# Lint code
flake8 app/

# Type check
mypy app/

# Start with auto-reload
python3 -m uvicorn app.main:app --reload
```

### Database

SQLite database stored at `./data/instances.db`:

```bash
# View contents
sqlite3 ./data/instances.db
sqlite> SELECT * FROM instances;

# Reset database
rm ./data/instances.db
```

## Troubleshooting

### Instance creation fails with "No default VPC"

AWS requires a default VPC. Create one:
```bash
aws ec2 create-default-vpc
```

### Can't SSH to instance

Check:
1. Security group allows port 22: [SSH_SETUP.md](docs/SSH_SETUP.md)
2. Instance is running: `aws ec2 describe-instances --instance-ids i-xxxxx`
3. Key pair exists: `ls -la ~/.ssh/my_ec2_keypair.pem`
4. Key permissions: `chmod 600 ~/.ssh/my_ec2_keypair.pem`

### Email notifications not sending

Check:
1. `.env` has valid SMTP credentials
2. Gmail app password (not main password)
3. 2-Factor authentication enabled on Gmail
4. Port 587 is not blocked by firewall

### Terraform fails with "Invalid AMI ID"

The AMI may not exist in your region. Use:
```bash
aws ec2 describe-images --owners amazon \
  --filters "Name=name,Values=amzn2-ami-*" \
  --region us-east-1
```

## Contributing

Contributions welcome! Please:
1. Follow the existing code style
2. Add tests for new features
3. Update documentation
4. Create a pull request with a clear description

## License

MIT License — See LICENSE file for details

## Support

For questions or issues:
1. Check the [docs/](docs/) directory
2. Review the [API_REFERENCE.md](docs/API_REFERENCE.md)
3. Check application logs: `docker-compose logs api`
4. Review AWS CloudTrail for infrastructure issues

---

**Last Updated:** February 2026
**Status:** Production-Ready ✅
