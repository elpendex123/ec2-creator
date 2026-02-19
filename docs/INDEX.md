# EC2 Provisioner Documentation Index

Quick reference to all documentation files.

## Getting Started

- **[QUICK_START.md](QUICK_START.md)** — Start in 5 minutes
  - Prerequisites and setup
  - Running the API locally
  - Creating your first instance
  - Backend selection
  - Free-tier configuration

## API Documentation

- **[API_REFERENCE.md](API_REFERENCE.md)** — Complete endpoint reference
  - All 6 endpoints (create, list, get, start, stop, destroy)
  - Request/response formats
  - Error codes and handling
  - Query parameters
  - Examples for each endpoint
  - Response field descriptions

## Operations

- **[SSH_SETUP.md](SSH_SETUP.md)** — SSH configuration and access
  - Key pair setup
  - SSH connection commands
  - Security group configuration
  - Troubleshooting SSH issues
  - Advanced configuration

- **[DEPLOYMENT.md](DEPLOYMENT.md)** — Multi-stage deployment
  - Stage 1: Local Linux
  - Stage 2: Docker + ECR
  - Stage 3: Minikube
  - Stage 4: Amazon EKS
  - Environment setup for each stage
  - Jenkins pipeline information
  - Verification steps
  - Troubleshooting by stage

## Project Information

- **[CHANGELOG.md](CHANGELOG.md)** — Version history and updates
  - Recent changes (v2.0)
  - Code fixes and improvements
  - New features
  - Files modified/created
  - Known limitations
  - Future roadmap

## Root Documentation

- **[../README.md](../README.md)** — Project overview
  - Tech stack
  - Features
  - Quick start
  - Project structure
  - Free-tier constraints
  - Development guide
  - Architecture overview
  - REST API endpoints
  - Query parameters
  - Bash script responsibilities
  - Key application behaviors
  - Recent updates

---

## Quick Navigation

### By Role

**Developers:**
1. Start with [QUICK_START.md](QUICK_START.md)
2. Explore [API_REFERENCE.md](API_REFERENCE.md)
3. Check [DEPLOYMENT.md](DEPLOYMENT.md) Stage 1
4. Review code in `app/` directory

**DevOps/Infrastructure:**
1. Read [DEPLOYMENT.md](DEPLOYMENT.md) all stages
2. Review Jenkins pipelines in `jenkins/`
3. Check Terraform configs in `terraform/`
4. Configure CI/CD pipelines

**System Administrators:**
1. [SSH_SETUP.md](SSH_SETUP.md) for access
2. [DEPLOYMENT.md](DEPLOYMENT.md) for operations
3. Kubernetes manifests in `k8s/`

**Security/Auditors:**
1. Review [SSH_SETUP.md](SSH_SETUP.md) security notes
2. Check [API_REFERENCE.md](API_REFERENCE.md) error handling
3. Review [CHANGELOG.md](CHANGELOG.md) for changes

### By Task

**I want to...**

- **Create an EC2 instance**
  → [QUICK_START.md](QUICK_START.md) (Local) or [DEPLOYMENT.md](DEPLOYMENT.md) (Production)

- **Access an instance via SSH**
  → [SSH_SETUP.md](SSH_SETUP.md)

- **Call the API**
  → [API_REFERENCE.md](API_REFERENCE.md)

- **Deploy to production**
  → [DEPLOYMENT.md](DEPLOYMENT.md) Stage 4 (EKS)

- **Set up local development**
  → [QUICK_START.md](QUICK_START.md) Stage 1

- **Use Docker**
  → [DEPLOYMENT.md](DEPLOYMENT.md) Stage 2

- **Test with Kubernetes locally**
  → [DEPLOYMENT.md](DEPLOYMENT.md) Stage 3

- **Understand recent changes**
  → [CHANGELOG.md](CHANGELOG.md)

- **Troubleshoot SSH issues**
  → [SSH_SETUP.md](SSH_SETUP.md) Troubleshooting section

- **Debug deployment issues**
  → [DEPLOYMENT.md](DEPLOYMENT.md) Troubleshooting by stage

---

## Document Statistics

| Document | Lines | Size | Purpose |
|----------|-------|------|---------|
| QUICK_START.md | 167 | 3.3K | 5-minute setup |
| API_REFERENCE.md | 407 | 8.5K | Complete API docs |
| SSH_SETUP.md | 229 | 5.2K | SSH & keys |
| DEPLOYMENT.md | 424 | 8.8K | 4-stage deployment |
| CHANGELOG.md | 268 | 8.0K | Version history |
| INDEX.md | 180 | 5.0K | This index |
| **Total** | **1675** | **39K** | **Complete docs** |

---

## Key Concepts

### Free-Tier Constraints
- **Allowed instance types:** t3.micro, t4g.micro
- **Whitelisted AMIs:** Per-region free-tier eligible AMIs
- **SSH key pair:** my_ec2_keypair (auto-configured)
- **Storage:** Any size >= 1 GB

### Dual Backend
Choose provisioning method per request:
- **AWS CLI** (default) — Direct AWS API, faster
- **Terraform** — Infrastructure as code, better for complex setups

### 4-Stage Deployment
1. **Local** — Native Linux, direct Python execution
2. **Docker** — Containerized, pushed to ECR
3. **Minikube** — Local Kubernetes testing
4. **EKS** — Production-grade Kubernetes on AWS

### Email Notifications
Automated emails on:
- Instance creation
- Instance start
- Instance stop
- Instance destruction

---

## FAQ Quick Links

**Q: How do I get started?**
A: [QUICK_START.md](QUICK_START.md)

**Q: How do I SSH to an instance?**
A: [SSH_SETUP.md](SSH_SETUP.md)

**Q: What are the API endpoints?**
A: [API_REFERENCE.md](API_REFERENCE.md)

**Q: How do I deploy to production?**
A: [DEPLOYMENT.md](DEPLOYMENT.md) — Stage 4

**Q: Why is my instance creation failing?**
A: See DEPLOYMENT.md Troubleshooting or [CHANGELOG.md](CHANGELOG.md) Known Limitations

**Q: Can I use a different key pair?**
A: Yes, see [SSH_SETUP.md](SSH_SETUP.md) "Updating Key Pair Configuration"

**Q: What instance types are free-tier?**
A: t3.micro and t4g.micro ([QUICK_START.md](QUICK_START.md))

**Q: How do I view instance details?**
A: Use GET `/instances/{instance_id}` ([API_REFERENCE.md](API_REFERENCE.md))

---

## Related Resources

- **Project Root:** [../](../)
- **Source Code:** `app/` — FastAPI application
- **Infrastructure Code:** `terraform/` — Terraform configs
- **Automation Scripts:** `aws_cli_bash_scripts/`, `terraform_bash_scripts/`
- **CI/CD:** `jenkins/` — Jenkins pipeline definitions
- **Kubernetes:** `k8s/` — Kubernetes manifests
- **Container:** `Dockerfile`, `docker-compose.yml`

---

**Last Updated:** February 19, 2026
**Maintainer:** Enrique
**Status:** Complete ✅
