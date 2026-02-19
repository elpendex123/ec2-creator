# Jenkins Local Pipelines — Quick Reference

## The 4 Pipelines

```
┌─────────────────────┐
│   BUILD PIPELINE    │  (10-15 min)
│ Jenkinsfile.local.  │
│        build        │
├─────────────────────┤
│ • Checkout code     │
│ • Setup Python venv │
│ • Install deps      │
│ • Lint (flake8)     │
│ • Unit tests        │
│ • Archive reports   │
└──────────┬──────────┘
           │ Success
           ↓
┌─────────────────────┐
│    QA PIPELINE      │  (5-10 min)
│ Jenkinsfile.local.  │
│         qa          │
├─────────────────────┤
│ • Coverage analysis │
│ • Security scan     │
│ • Dependency check  │
│ • Quality metrics   │
│ • Archive reports   │
└──────────┬──────────┘
           │ Success
           ↓
┌─────────────────────┐
│  DEPLOY PIPELINE    │  (5-10 min)
│ Jenkinsfile.local.  │
│       deploy        │
├─────────────────────┤
│ • Start API server  │
│ • Health checks     │
│ • Verify endpoints  │
│ • Server: 8000      │
└──────────┬──────────┘
           │ Success
           ↓
┌─────────────────────┐
│   TEST PIPELINE     │  (5-10 min)
│ Jenkinsfile.local.  │
│ integration-test    │
├─────────────────────┤
│ • Run test_api.py   │
│ • Validate endpoints│
│ • Performance check │
│ • Test reports      │
└─────────────────────┘
           │ Success
           ↓
        ✓ READY
```

---

## What Each Pipeline Does

### 1️⃣ BUILD PIPELINE — `Jenkinsfile.local.build`

**Purpose:** Prepare and test the codebase

**Key Steps:**
```
Code → Python venv → Dependencies → Linting → Unit Tests → Reports
```

**Checks:**
- ✓ Code passes flake8
- ✓ Unit tests pass
- ✓ Coverage metrics generated

**Triggers Next:** QA Pipeline

---

### 2️⃣ QA PIPELINE — `Jenkinsfile.local.qa`

**Purpose:** Ensure code quality and security

**Key Steps:**
```
Venv → Coverage Analysis → Security Scan → Dependency Check → Reports
```

**Checks:**
- ✓ Coverage ≥ 70%
- ✓ No hardcoded secrets
- ✓ Dependencies up to date

**Triggers Next:** Deployment Pipeline

---

### 3️⃣ DEPLOYMENT PIPELINE — `Jenkinsfile.local.deploy`

**Purpose:** Start the API server locally

**Key Steps:**
```
Kill old process → Start uvicorn → Health check → Verify endpoints → Ready
```

**Result:**
- ✓ Server running on `http://localhost:8000`
- ✓ Swagger UI at `http://localhost:8000/docs`
- ✓ Logs in `${WORKSPACE}/app.log`

**Triggers Next:** Integration Test Pipeline

---

### 4️⃣ INTEGRATION TEST PIPELINE — `Jenkinsfile.local.integration-test`

**Purpose:** Test the deployed API

**Key Steps:**
```
Wait for server → Run test_api.py → Validate endpoints → Performance check → Reports
```

**Tests Run:**
- ✓ Health endpoint
- ✓ List instances
- ✓ Invalid instance type detection
- ✓ Invalid AMI detection
- ✓ Swagger UI

**Final Output:**
- ✓ All tests passed OR ✗ Some tests failed

---

## How to Use

### Start Full Pipeline Chain

```bash
# In Jenkins UI
1. Go to: http://jenkins:8080/job/ec2-creator-build
2. Click "Build Now"
3. Wait ~40 minutes for all 4 pipelines to complete
```

Or with curl:
```bash
curl -X POST http://jenkins:8080/job/ec2-creator-build/build \
  -u username:token
```

### Run Individual Pipeline

```bash
# Build only
curl -X POST http://jenkins:8080/job/ec2-creator-build/build -u user:token

# QA only (requires build artifacts)
curl -X POST http://jenkins:8080/job/ec2-creator-qa/build -u user:token

# Deploy only (requires source code)
curl -X POST http://jenkins:8080/job/ec2-creator-deploy-local/build -u user:token

# Integration tests only (requires running API)
curl -X POST http://jenkins:8080/job/ec2-creator-integration-test/build -u user:token
```

---

## File Locations

### Pipeline Files
```
jenkins/deployment/
├── Jenkinsfile.local.build                    (Build)
├── Jenkinsfile.local.qa                       (QA)
├── Jenkinsfile.local.deploy                   (Deploy)
└── Jenkinsfile.local.integration-test         (Integration Test)
```

### Test Files
```
tests/
├── __init__.py
└── test_*.py                                  (Your unit tests)

test_api.py                                    (Integration tests)
```

### Generated Artifacts
```
build-artifacts/
  ├── test-results.xml
  ├── coverage.xml
  └── flake8-report.json

qa-artifacts/
  └── coverage-report/
      └── index.html

${WORKSPACE}/
  ├── app.log                                  (Server logs)
  └── api.pid                                  (Server process ID)

integration-artifacts/
  ├── integration-test-results.txt
  └── test-reports/
      └── integration-summary.txt
```

---

## Timeline Example

```
Start: 0:00  →  Build starts
       0:15  →  ✓ Build done  →  QA starts
       0:25  →  ✓ QA done     →  Deploy starts
       0:35  →  ✓ Deploy done →  Tests start
       0:40  →  ✓ Tests done  →  ALL COMPLETE ✓
```

**Total duration:** ~40 minutes from start to finish

---

## Success/Failure Indicators

### All Green ✓
```
BUILD ✓ → QA ✓ → DEPLOY ✓ → TEST ✓
API running at: http://localhost:8000
Swagger UI: http://localhost:8000/docs
Ready for next stage (Docker/Kubernetes)
```

### Build Failed ✗
```
BUILD ✗ (linting or unit test failed)
→ Pipeline stops, QA/Deploy/Test do not run
→ Fix code issues and retry
```

### QA Failed ✗
```
BUILD ✓ → QA ✗ (coverage < 70% or security issue)
→ Pipeline stops, Deploy/Test do not run
→ Add more tests or fix security issues
```

### Deploy Failed ✗
```
BUILD ✓ → QA ✓ → DEPLOY ✗ (port in use or server crash)
→ Pipeline stops, Test does not run
→ Kill existing process: lsof -ti:8000 | xargs kill -9
→ Retry deployment
```

### Test Failed ✗
```
BUILD ✓ → QA ✓ → DEPLOY ✓ → TEST ✗
→ Some API tests failed
→ Review test results, check API logs
→ Fix API code and retry from Build

API still running at: http://localhost:8000
Logs at: ${WORKSPACE}/app.log
```

---

## Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Port 8000 in use | `lsof -ti:8000 \| xargs kill -9` |
| Tests failing | Check `test_api.py` output and API logs |
| Coverage too low | Add more unit tests to `tests/` |
| Build slow | Check network for pip install bottleneck |
| API won't start | `tail app.log` to see error |

---

## Next Steps

After all 4 pipelines pass:

### 1. Deploy to Docker
```bash
# Use Jenkinsfile.docker
# Builds image, runs docker-compose, pushes to ECR
```

### 2. Deploy to Minikube
```bash
# Use Jenkinsfile.minikube
# Pulls from ECR, deploys to local Kubernetes
```

### 3. Deploy to EKS
```bash
# Use Jenkinsfile.eks
# Provisions EKS cluster, deploys to production AWS
```

---

## Key Commands

### View API Status
```bash
curl http://localhost:8000/health
```

### View Instances
```bash
curl http://localhost:8000/instances
```

### View Server Logs
```bash
tail -f app.log
```

### Kill Server
```bash
kill $(cat api.pid)
```

### Run Tests Manually
```bash
source venv/bin/activate
python test_api.py
```

---

## Environment

- **Python:** 3.11+
- **API Port:** 8000
- **API Host:** localhost
- **Framework:** FastAPI with uvicorn
- **Test Framework:** pytest
- **Linter:** flake8

---

**Documentation:** See `docs/JENKINS_LOCAL_PIPELINES.md` for detailed information.
