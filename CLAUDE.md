# CLAUDE.md — EC2 Provisioner API

## Project Overview
A FastAPI REST API that provisions and manages AWS EC2 instances via Terraform and AWS CLI bash scripts. The app is deployed progressively across 4 stages: local Linux → Docker (local + ECR push) → Minikube → EKS. Jenkins pipelines cover both app deployment and EC2 lifecycle operations via two parallel toolsets (Terraform and AWS CLI).

---

## Tech Stack
- **Python 3.11+** with **FastAPI** — REST API
- **Terraform** — EC2 provisioning, lifecycle management, EKS cluster setup
- **AWS CLI + Bash** — parallel EC2 operations independent of Terraform
- **Docker + Docker Compose** — local containerized deployment
- **Amazon ECR** — Docker image registry (populated at Stage 2, consumed by Stages 3 and 4)
- **Kubernetes / minikube** — local k8s testing
- **Amazon EKS** — production Kubernetes on AWS
- **SQLite** — local persistence for instance records
- **Python subprocess** — invokes Terraform CLI and AWS CLI from FastAPI
- **smtplib (SMTP)** — email notifications on lifecycle events
- **Jenkins** — CI/CD pipelines for deployment stages and EC2 operation jobs

---

## Project Structure
```
ec2-provisioner/
├── app/
│   ├── main.py                        # FastAPI app entry point, router registration
│   ├── config.py                      # Load .env vars, expose settings object
│   ├── routers/
│   │   └── instances.py               # All /instances endpoints
│   ├── services/
│   │   ├── terraform.py               # subprocess calls to terraform_bash_scripts/
│   │   ├── aws_cli.py                 # subprocess calls to aws_cli_bash_scripts/
│   │   ├── db.py                      # SQLite CRUD: create, read, update, delete instance records
│   │   └── notifications.py           # SMTP email sender
│   └── models/
│       └── instance.py                # Pydantic request/response models
│
├── terraform/
│   ├── ec2/
│   │   ├── main.tf                    # aws_instance resource
│   │   ├── variables.tf               # ami, instance_type, storage_gb, name
│   │   └── outputs.tf                 # public_ip, instance_id
│   └── eks/
│       ├── main.tf                    # EKS cluster + node group
│       ├── variables.tf               # cluster_name, region, node instance type
│       └── outputs.tf                 # cluster_endpoint, kubeconfig
│
├── terraform_bash_scripts/            # Wrap Terraform CLI — mirror of aws_cli_bash_scripts
│   ├── tf_init.sh                     # terraform init
│   ├── tf_create.sh                   # write tfvars + terraform apply
│   ├── tf_list.sh                     # terraform show, parse state for instance list
│   ├── tf_start.sh                    # start instance via terraform taint + apply
│   ├── tf_stop.sh                     # stop instance via resource update
│   └── tf_destroy.sh                  # terraform destroy -auto-approve
│
├── aws_cli_bash_scripts/              # Pure AWS CLI — no Terraform dependency
│   ├── create_instance.sh             # aws ec2 run-instances
│   ├── list_instances.sh              # aws ec2 describe-instances
│   ├── start_instance.sh              # aws ec2 start-instances
│   ├── stop_instance.sh               # aws ec2 stop-instances
│   └── destroy_instance.sh            # aws ec2 terminate-instances
│
├── jenkins/
│   ├── deployment/
│   │   ├── Jenkinsfile.local          # Stage 1: lint → test → uvicorn start
│   │   ├── Jenkinsfile.docker         # Stage 2: build → compose up → tag → push to ECR
│   │   ├── Jenkinsfile.minikube       # Stage 3: pull from ECR → kubectl apply to minikube
│   │   └── Jenkinsfile.eks            # Stage 4: terraform eks apply → kubeconfig → kubectl apply
│   ├── terraform_jobs/
│   │   ├── Jenkinsfile.tf_create      # runs tf_create.sh
│   │   ├── Jenkinsfile.tf_list        # runs tf_list.sh
│   │   ├── Jenkinsfile.tf_start       # runs tf_start.sh
│   │   ├── Jenkinsfile.tf_stop        # runs tf_stop.sh
│   │   └── Jenkinsfile.tf_destroy     # runs tf_destroy.sh
│   └── aws_cli_jobs/
│       ├── Jenkinsfile.cli_create     # runs create_instance.sh
│       ├── Jenkinsfile.cli_list       # runs list_instances.sh
│       ├── Jenkinsfile.cli_start      # runs start_instance.sh
│       ├── Jenkinsfile.cli_stop       # runs stop_instance.sh
│       └── Jenkinsfile.cli_destroy    # runs destroy_instance.sh
│
├── k8s/
│   ├── deployment.yaml                # image: <ECR_REPO>:<ECR_IMAGE_TAG>
│   ├── service.yaml                   # NodePort for minikube, LoadBalancer for EKS
│   └── configmap.yaml                 # non-secret env vars
│
├── Dockerfile                         # multi-stage: build + slim runtime image
├── docker-compose.yml                 # api service + SQLite named volume
├── requirements.txt
├── .env.example
└── CLAUDE.md
```

---

## REST API Endpoints

| Method   | Endpoint                  | Description                        |
|----------|---------------------------|------------------------------------|
| `POST`   | `/instances`              | Create a new EC2 instance          |
| `GET`    | `/instances`              | List all instances                 |
| `GET`    | `/instances/{id}`         | Get details of one instance        |
| `POST`   | `/instances/{id}/start`   | Start a stopped instance           |
| `POST`   | `/instances/{id}/stop`    | Stop a running instance            |
| `DELETE` | `/instances/{id}`         | Destroy/terminate an instance      |

### Query Parameter
All endpoints accept `?backend=terraform` or `?backend=awscli` to select the implementation. If omitted, the `BACKEND` env var is used as the default.

### POST `/instances` Request Body
```json
{
  "name": "my-dev-server",
  "ami": "ami-0c02fb55956c7d316",
  "instance_type": "t2.micro",
  "storage_gb": 8
}
```

### POST `/instances` Response
```json
{
  "id": "i-0abc123def456",
  "name": "my-dev-server",
  "public_ip": "54.123.45.67",
  "ssh_string": "ssh -i ~/.ssh/your-key.pem ec2-user@54.123.45.67",
  "state": "running",
  "ami": "ami-0c02fb55956c7d316",
  "instance_type": "t2.micro",
  "backend_used": "terraform",
  "created_at": "2025-01-01T12:00:00Z"
}
```

---

## The 4 Deployment Stages

### Stage 1 — Local Linux
- Run FastAPI directly on Linux with `uvicorn app.main:app --reload`
- Terraform and AWS CLI installed natively on the machine
- No Docker, no ECR
- Jenkins pipeline: lint (`flake8`) → test (`pytest`) → start uvicorn process

### Stage 2 — Docker Locally + ECR Push
- App runs in Docker via `docker-compose up`
- SQLite persisted via named Docker volume
- AWS credentials injected from `.env`
- Jenkins pipeline: build image → `docker-compose up` → `aws ecr get-login-password` → tag image → `docker push` to ECR
- **This is the only stage that builds and pushes the image to ECR**

### Stage 3 — Minikube (local Kubernetes)
- App deployed to minikube cluster
- Jenkins pipeline: configure ECR credentials in minikube → `kubectl apply` all manifests in `k8s/`
- Service type: `NodePort`
- Image source: ECR (no local build)
- minikube must have ECR pull secret configured

### Stage 4 — EKS (production)
- Terraform provisions EKS cluster using `terraform/eks/`
- Jenkins pipeline: `terraform apply` (eks) → `aws eks update-kubeconfig` → `kubectl apply` all manifests
- Service type: `LoadBalancer` (AWS ALB)
- Image source: ECR (same image pushed in Stage 2)
- No image build in this stage

### ECR Image Flow Summary
```
Stage 2  →  docker build  →  docker-compose up (local test)  →  docker push to ECR
Stage 3  →  minikube pulls from ECR  →  kubectl apply
Stage 4  →  EKS pulls from ECR  →  kubectl apply
```

---

## Jenkins Pipelines Detail

### Deployment Pipelines (`jenkins/deployment/`)

**Jenkinsfile.local**
```
Stages: Checkout → Lint (flake8) → Test (pytest) → Start (uvicorn)
```

**Jenkinsfile.docker**
```
Stages: Checkout → Lint → Test → Docker Build → Docker Compose Up → ECR Login → Tag → Push to ECR
```

**Jenkinsfile.minikube**
```
Stages: Checkout → ECR Login → Configure minikube ECR secret → kubectl apply → Verify pods running
```

**Jenkinsfile.eks**
```
Stages: Checkout → Terraform Init (eks/) → Terraform Apply (eks/) → Update kubeconfig → kubectl apply → Verify deployment
```

### Terraform EC2 Operation Jobs (`jenkins/terraform_jobs/`)
Each job takes parameters (instance_id, name, ami, etc.) and runs the corresponding script:
- `Jenkinsfile.tf_create` → params: name, ami, instance_type, storage_gb
- `Jenkinsfile.tf_list` → no params required
- `Jenkinsfile.tf_start` → params: instance_id
- `Jenkinsfile.tf_stop` → params: instance_id
- `Jenkinsfile.tf_destroy` → params: instance_id

### AWS CLI EC2 Operation Jobs (`jenkins/aws_cli_jobs/`)
Each job takes the same parameters as the Terraform equivalents:
- `Jenkinsfile.cli_create` → params: name, ami, instance_type, storage_gb
- `Jenkinsfile.cli_list` → no params required
- `Jenkinsfile.cli_start` → params: instance_id
- `Jenkinsfile.cli_stop` → params: instance_id
- `Jenkinsfile.cli_destroy` → params: instance_id

---

## Bash Script Responsibilities

### `aws_cli_bash_scripts/` — Pure AWS CLI, no Terraform
- `create_instance.sh` — accepts name, ami, instance_type, storage_gb as args; runs `aws ec2 run-instances`; outputs instance_id and public_ip
- `list_instances.sh` — runs `aws ec2 describe-instances`; outputs table of id, state, public_ip, launch_time
- `start_instance.sh` — accepts instance_id; runs `aws ec2 start-instances`; waits for running state
- `stop_instance.sh` — accepts instance_id; runs `aws ec2 stop-instances`; waits for stopped state
- `destroy_instance.sh` — accepts instance_id; runs `aws ec2 terminate-instances`; confirms termination

### `terraform_bash_scripts/` — Terraform CLI wrappers
- `tf_init.sh` — runs `terraform init` in `terraform/ec2/`
- `tf_create.sh` — accepts name, ami, instance_type, storage_gb; writes `.tfvars` file; runs `terraform apply -auto-approve`; outputs public_ip and instance_id from `terraform output`
- `tf_list.sh` — runs `terraform show -json`; parses and prints instance details
- `tf_start.sh` — accepts instance_id; uses AWS CLI under the hood (Terraform doesn't natively start/stop)
- `tf_stop.sh` — accepts instance_id; uses AWS CLI under the hood
- `tf_destroy.sh` — accepts instance_id or workspace name; runs `terraform destroy -auto-approve`

---

## Key Application Behaviors

### Free Tier Enforcement
- Allowed instance types: `t2.micro`, `t3.micro` only
- AMI validation: check against a maintained list of known free-tier AMIs per region
- Return HTTP `400` with descriptive error if invalid type or AMI is passed

### SQLite Schema
Table: `instances`
```
id            TEXT PRIMARY KEY   -- AWS instance ID (i-xxxx)
name          TEXT
public_ip     TEXT
ami           TEXT
instance_type TEXT
state         TEXT               -- running, stopped, terminated
ssh_string    TEXT
backend_used  TEXT               -- terraform or awscli
created_at    TIMESTAMP
updated_at    TIMESTAMP
```

### SSH String Format
```
ssh -i ~/.ssh/your-key.pem ec2-user@<public_ip>
```
Returned in every create response and stored in SQLite.

### Email Notifications
Sent via SMTP on: create, start, stop, destroy. Email includes instance ID, name, public IP, state, and timestamp. Uses Python `smtplib` with credentials from `.env`.

### Backend Switching
- Default backend set via `BACKEND` env var (`terraform` or `awscli`)
- Overridable per request: `POST /instances?backend=awscli`
- FastAPI router checks param → calls either `services/terraform.py` or `services/aws_cli.py`

---

## curl Examples
```bash
# Create instance (terraform backend)
curl -X POST http://localhost:8000/instances \
  -H "Content-Type: application/json" \
  -d '{"name":"dev-box","ami":"ami-0c02fb55956c7d316","instance_type":"t2.micro","storage_gb":8}'

# Create instance (awscli backend)
curl -X POST "http://localhost:8000/instances?backend=awscli" \
  -H "Content-Type: application/json" \
  -d '{"name":"dev-box","ami":"ami-0c02fb55956c7d316","instance_type":"t2.micro","storage_gb":8}'

# List all instances
curl http://localhost:8000/instances

# Get one instance
curl http://localhost:8000/instances/i-0abc123def456

# Start instance
curl -X POST http://localhost:8000/instances/i-0abc123def456/start

# Stop instance
curl -X POST http://localhost:8000/instances/i-0abc123def456/stop

# Destroy instance
curl -X DELETE http://localhost:8000/instances/i-0abc123def456
```

---

## Environment Variables (`.env`)
```bash
# AWS credentials
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_DEFAULT_REGION=us-east-1

# SMTP email notifications
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
NOTIFICATION_EMAIL=

# App config
BACKEND=terraform              # default backend: terraform or awscli

# ECR / EKS
ECR_REPO=                      # e.g. 123456789.dkr.ecr.us-east-1.amazonaws.com/ec2-provisioner
ECR_IMAGE_TAG=latest
EKS_CLUSTER_NAME=              # e.g. ec2-provisioner-cluster
```

---

## Docker Compose Notes
- Service: `api` — built from `Dockerfile`, exposes port 8000
- Volume: named volume `sqlite_data` mounted at `/app/data` for SQLite persistence
- `.env` file loaded automatically by Compose
- AWS credentials and SMTP config injected as environment variables into the container

## Kubernetes Notes
- `deployment.yaml` image field must use full ECR URI: `<ECR_REPO>:<ECR_IMAGE_TAG>`
- `service.yaml` should support both NodePort (minikube) and LoadBalancer (EKS) — use separate overlays or a single file with a comment indicating which type to use per environment
- `configmap.yaml` holds non-secret env vars (region, backend default, etc.)
- ECR pull secret must be created in the k8s namespace before deploying to minikube or EKS

## Terraform Notes
- `terraform/ec2/` — manages individual EC2 instances; state stored locally as `terraform.tfstate`
- `terraform/eks/` — manages the EKS cluster and node group; state stored locally
- Each `tf_create.sh` invocation should use a unique Terraform workspace per instance to avoid state collisions
- All Terraform runs use local state (no S3 backend)

---

## Dependencies (`requirements.txt`)
```
fastapi
uvicorn[standard]
pydantic
python-dotenv
pytest
httpx
flake8
```

---

## Recent Updates (February 2026)

### Code Fixes
- ✅ Updated `ALLOWED_INSTANCE_TYPES` to `["t3.micro", "t4g.micro"]` (t2.micro is not free-tier eligible)
- ✅ Added `ami-026992d753d5622bc` (current Amazon Linux 2) to `FREE_TIER_AMIS["us-east-1"]`
- ✅ Fixed stdout pollution in `create_instance.sh` (redirected status messages to stderr)
- ✅ Made `InstanceResponse.public_ip` and `ssh_string` Optional fields
- ✅ Added defensive instance ID parsing to strip extra newlines
- ✅ Updated error messages to reflect correct free-tier instance types
- ✅ Added SSH key pair support: all instances created with `my_ec2_keypair`

### Script Updates
- ✅ `aws_cli_bash_scripts/create_instance.sh` — Added `--key-name my_ec2_keypair`
- ✅ `terraform_bash_scripts/tf_create.sh` — Added `key_name` to tfvars
- ✅ `terraform/ec2/main.tf` — Added `key_name` variable to aws_instance resource
- ✅ `terraform/ec2/variables.tf` — Added `key_name` variable definition

### Documentation (New `docs/` Directory)
- ✅ `docs/QUICK_START.md` — Get started in 5 minutes
- ✅ `docs/API_REFERENCE.md` — Complete endpoint documentation with examples
- ✅ `docs/SSH_SETUP.md` — SSH key pair configuration and troubleshooting
- ✅ `docs/DEPLOYMENT.md` — Stage-by-stage deployment instructions (Local → Docker → Minikube → EKS)
- ✅ `README.md` (root) — Project overview with links to all documentation

### Tested Features
- ✅ Instance creation with correct free-tier validation
- ✅ SSH access with my_ec2_keypair
- ✅ Email notifications (SMTP)
- ✅ List, get, start, stop, destroy endpoints
- ✅ Dual backend support (awscli and terraform)

---

## Notes for Claude Code
- Implement all 6 REST endpoints with full request validation using Pydantic models
- Both `services/terraform.py` and `services/aws_cli.py` must implement the same interface so the router can call either transparently
- All bash scripts must be executable (`chmod +x`) and accept arguments positionally
- Jenkins Jenkinsfiles should use declarative pipeline syntax
- Free tier validation should be a shared utility function called by both backends
- SQLite database file should be stored at the path defined in config, defaulting to `./data/instances.db`
- Email notifications should be non-blocking (use background tasks in FastAPI)
- Include a `/health` endpoint that returns `{"status": "ok"}` for k8s liveness probes
- All Terraform workspaces should be named after the instance `name` field to keep state isolated per instance
- SSH key pair `my_ec2_keypair` must be configured in both AWS CLI and Terraform scripts
- All documentation should be in `docs/` directory organized by topic
