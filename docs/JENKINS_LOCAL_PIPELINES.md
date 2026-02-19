# Local Deployment Pipeline Strategy

Complete breakdown of Jenkins pipelines for building, testing, and deploying the EC2 Creator API locally.

## Overview

The local deployment uses **4 interconnected pipelines** that work together in sequence:

```
Build Pipeline → QA Pipeline → Deployment Pipeline → Integration Test Pipeline
```

Each pipeline is independent but triggers the next one on success, creating a complete CI/CD workflow.

---

## Pipeline 1: Build Pipeline

**File:** `jenkins/deployment/Jenkinsfile.local.build`

**Purpose:** Install dependencies, lint code, and run unit tests

**Trigger:** Manual or webhook on code push

### Stages

| Stage | Purpose | Actions |
|-------|---------|---------|
| **Checkout** | Get source code | Clone repository |
| **Setup Environment** | Create Python venv | Create virtual environment with Python 3.11 |
| **Install Dependencies** | Install packages | Install from `requirements.txt` (FastAPI, pytest, etc.) |
| **Lint Code** | Code quality check | Run flake8 on `app/` directory |
| **Unit Tests** | Run tests | Execute pytest, generate coverage reports |
| **Archive Artifacts** | Save reports | Store test results, coverage XML, flake8 reports |

### Key Features

- **Clean environment:** Fresh virtual environment per build
- **Code coverage:** Generates HTML coverage reports (requires tests to exist)
- **Linting:** Detects code style issues with flake8
- **Artifact archiving:** Saves all reports for review
- **Auto-trigger next:** On success, triggers QA pipeline

### Configuration

```bash
# Environment variables set
PYTHON_VERSION = '3.11'
PROJECT_NAME = 'ec2-creator'
VENV_DIR = '${WORKSPACE}/venv'

# Timeout: 15 minutes
# Keep last: 10 builds
```

### Success Criteria

✓ Code passes flake8 linting
✓ All unit tests pass
✓ Code coverage > 0% (configurable)

### Run Manually

```bash
curl -X POST http://jenkins:8080/job/ec2-creator-build/build \
  -u username:token
```

---

## Pipeline 2: QA Pipeline

**File:** `jenkins/deployment/Jenkinsfile.local.qa`

**Purpose:** Perform code quality analysis and security scanning

**Trigger:** Automatically on Build pipeline success

### Stages

| Stage | Purpose | Actions |
|-------|---------|---------|
| **Checkout** | Get source code | Clone repository |
| **Setup Environment** | Create Python venv | Install dependencies silently |
| **Code Coverage Analysis** | Coverage report | Run pytest with coverage metrics, enforce minimum threshold (70%) |
| **Security Scanning** | Detect vulnerabilities | Check for hardcoded secrets, SQL injection patterns |
| **Dependency Check** | Vulnerability scanning | Check for outdated packages and known vulnerabilities |
| **Code Quality Metrics** | Generate metrics | Count lines of code, number of test files |
| **Archive QA Reports** | Save reports | Store coverage and security reports |

### Key Features

- **Coverage enforcement:** Fails if coverage < 70% (configurable)
- **Secret detection:** Basic pattern matching for API keys, passwords
- **Dependency audit:** Lists outdated packages
- **Auto-trigger next:** On success, triggers Deployment pipeline

### Configuration

```bash
# Coverage threshold: 70%
# Timeout: 10 minutes
# Keep last: 10 builds
```

### Success Criteria

✓ Code coverage ≥ 70%
✓ No hardcoded secrets detected
✓ Dependency audit passed

### Coverage Report

Generated at: `coverage-report/index.html`

---

## Pipeline 3: Deployment Pipeline

**File:** `jenkins/deployment/Jenkinsfile.local.deploy`

**Purpose:** Start FastAPI server locally with health checks

**Trigger:** Automatically on QA pipeline success

### Stages

| Stage | Purpose | Actions |
|-------|---------|---------|
| **Checkout** | Get source code | Clone repository |
| **Setup Environment** | Create Python venv | Install dependencies |
| **Pre-Deployment Checks** | Verify readiness | Kill existing process on port 8000, verify app structure |
| **Start API Server** | Launch app | Start uvicorn on `localhost:8000` |
| **Health Check** | Verify startup | Poll `/health` endpoint (max 10 retries, 2s intervals) |
| **Verify API Endpoints** | Test endpoints | Test `/health`, `/instances`, `/docs` endpoints |
| **Deployment Summary** | Report status | Show API URLs and log file paths |

### Key Features

- **Port cleanup:** Kills any existing process on 8000 before starting
- **Health check polling:** Retries 10 times with 2-second intervals
- **Endpoint validation:** Tests key endpoints after startup
- **Background execution:** Server runs in background via nohup
- **Auto-trigger next:** On success, triggers Integration Test pipeline

### Configuration

```bash
# API Server
API_HOST = 'localhost'
API_PORT = '8000'

# Server logs written to: ${WORKSPACE}/app.log
# Server PID saved to: ${WORKSPACE}/api.pid

# Timeout: 20 minutes
# Keep last: 5 builds
```

### Server Details

```
URL: http://localhost:8000
Swagger UI: http://localhost:8000/docs
ReDoc: http://localhost:8000/redoc
Logs: ${WORKSPACE}/app.log
PID: ${WORKSPACE}/api.pid
```

### Success Criteria

✓ Server starts without errors
✓ `/health` endpoint responds with 200 OK
✓ `/instances` endpoint is accessible
✓ Swagger UI loads successfully

### Kill Server (When Needed)

```bash
# Option 1: Read PID from file
kill $(cat api.pid)

# Option 2: Kill by port
lsof -ti:8000 | xargs kill -9
```

---

## Pipeline 4: Integration Test Pipeline

**File:** `jenkins/deployment/Jenkinsfile.local.integration-test`

**Purpose:** Run API integration tests against the deployed server

**Trigger:** Automatically on Deployment pipeline success

### Stages

| Stage | Purpose | Actions |
|-------|---------|---------|
| **Checkout** | Get source code | Clone repository |
| **Setup Environment** | Create Python venv | Install dependencies |
| **Pre-Test Verification** | Check API | Verify server is running on port 8000 |
| **Run Integration Tests** | Execute tests | Run `test_api.py` script, capture results |
| **Run Endpoint Validation** | Validate endpoints | Test all major endpoints directly |
| **Performance Checks** | Measure latency | Time responses from key endpoints |
| **Generate Test Report** | Create report | Compile test results into summary document |
| **Archive Test Results** | Save results | Store all test artifacts |

### Key Features

- **Pre-test wait:** Retries 5 times to connect to API
- **Integration tests:** Runs `test_api.py` which tests all CRUD operations
- **Endpoint validation:** Direct curl tests to verify responses
- **Performance metrics:** Measures response times
- **Test reporting:** Generates comprehensive test report
- **Success/failure messaging:** Shows clear status at end

### Configuration

```bash
API_HOST = 'localhost'
API_PORT = '8000'
API_URL = 'http://localhost:8000'

# Timeout: 15 minutes
# Keep last: 10 builds
```

### Integration Tests (test_api.py)

```
1. Health Check - GET /health
2. List Instances - GET /instances
3. Invalid Instance Type - POST /instances with t2.large (should fail)
4. Invalid AMI - POST /instances with invalid AMI (should fail)
5. Swagger Docs - GET /docs
```

### Success Criteria

✓ All 5 integration tests pass
✓ All endpoints respond with correct status codes
✓ Performance is within acceptable ranges

### Test Results Location

```
test-reports/integration-summary.txt
```

---

## Complete Workflow Example

### Starting a Full Local Deployment

```bash
# Option 1: Trigger Build pipeline in Jenkins UI
# - Visit: http://jenkins:8080/job/ec2-creator-build
# - Click "Build Now"

# Option 2: Use curl
curl -X POST http://jenkins:8080/job/ec2-creator-build/build \
  -u username:token
```

### Pipeline Execution Flow

```
Time    Event                                Status
────────────────────────────────────────────────────
0:00    Build pipeline starts                [RUNNING]
0:05    Dependencies installed              [RUNNING]
0:08    Linting completed                   [RUNNING]
0:12    Unit tests completed                [RUNNING]
0:15    ✓ Build complete                    [SUCCESS]
        → Triggers QA pipeline
────────────────────────────────────────────────────
0:16    QA pipeline starts                  [RUNNING]
0:18    Coverage analysis: 75%              [RUNNING]
0:20    Security scanning                   [RUNNING]
0:23    ✓ QA complete                       [SUCCESS]
        → Triggers Deployment pipeline
────────────────────────────────────────────────────
0:24    Deploy pipeline starts              [RUNNING]
0:26    API server starting...              [RUNNING]
0:29    Health check: ✓                     [RUNNING]
0:30    ✓ Deployment complete               [SUCCESS]
        → Triggers Integration Test pipeline
────────────────────────────────────────────────────
0:31    Integration test pipeline starts    [RUNNING]
0:33    Running test_api.py                 [RUNNING]
0:38    5/5 tests passed                    [RUNNING]
0:40    ✓ All tests passed                  [SUCCESS]
────────────────────────────────────────────────────
Total time: ~40 minutes from start to finish
API ready at: http://localhost:8000
```

---

## Pipeline Interdependencies

```
Build Pipeline
  ├─ Generates: test-results.xml, coverage.xml, flake8-report.json
  └─ Success triggers: QA Pipeline

QA Pipeline
  ├─ Requires: Source code from Build
  ├─ Generates: coverage-report/, qa-artifacts/
  └─ Success triggers: Deployment Pipeline

Deployment Pipeline
  ├─ Requires: Clean source code
  ├─ Generates: app.log, api.pid
  ├─ Exposes: http://localhost:8000
  └─ Success triggers: Integration Test Pipeline

Integration Test Pipeline
  ├─ Requires: Running API server
  ├─ Generates: test-reports/, integration-test-results.txt
  └─ Final output: Pass/Fail status
```

---

## Environment Variables Reference

### Available in All Pipelines

```bash
PYTHON_VERSION = '3.11'
PROJECT_NAME = 'ec2-creator'
VENV_DIR = '${WORKSPACE}/venv'
```

### Deployment Pipeline Specific

```bash
API_PORT = '8000'
API_HOST = 'localhost'
```

### Integration Test Pipeline Specific

```bash
API_URL = 'http://localhost:8000'
```

---

## Artifact Locations

### Build Pipeline Artifacts

```
build-artifacts/
  ├─ test-results.xml          # JUnit test results
  ├─ coverage.xml              # Coverage in XML format
  └─ flake8-report.json        # Linting results
```

### QA Pipeline Artifacts

```
qa-artifacts/
  └─ coverage-report/          # HTML coverage report
      ├─ index.html
      ├─ status.json
      └─ ...
```

### Deployment Pipeline Artifacts

```
${WORKSPACE}/
  ├─ app.log                   # Server logs
  └─ api.pid                   # Server process ID
```

### Integration Test Pipeline Artifacts

```
integration-artifacts/
  ├─ integration-test-results.txt
  └─ test-reports/
      └─ integration-summary.txt
```

---

## Troubleshooting

### Pipeline 1: Build fails on "Unit Tests"

**Cause:** Tests directory may not exist

**Solution:**
```bash
# Create tests directory
mkdir -p tests
touch tests/__init__.py

# Add basic test
cat > tests/test_health.py <<'EOF'
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
EOF
```

### Pipeline 3: Deployment fails - "Port already in use"

**Cause:** Another process is using port 8000

**Solution:**
```bash
# Kill existing process
lsof -ti:8000 | xargs kill -9

# Or change port in deployment stage
# Modify API_PORT = '8001'
```

### Pipeline 4: Integration tests fail - "API not responding"

**Cause:** API server didn't start or crashed

**Check:**
```bash
# View server logs
tail -50 app.log

# Check if process is running
ps aux | grep uvicorn

# Manually start server
python -m uvicorn app.main:app --reload
```

---

## Manual Testing Without Jenkins

If you want to run the stages manually without Jenkins:

### Stage 1: Build

```bash
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
flake8 app/ --max-line-length=120
pytest tests/ -v
```

### Stage 2: QA

```bash
. venv/bin/activate
pytest tests/ --cov=app --cov-report=html
# Coverage report in: htmlcov/index.html
```

### Stage 3: Deploy

```bash
. venv/bin/activate
python -m uvicorn app.main:app --reload
# Server at http://localhost:8000
```

### Stage 4: Integration Tests

```bash
. venv/bin/activate
python test_api.py
```

---

## Next Steps After All Pipelines Succeed

Once all 4 pipelines pass locally:

1. **Deploy to Docker** (Local Container)
   - Use `Jenkinsfile.docker`
   - Builds image, runs in docker-compose
   - Pushes to ECR

2. **Deploy to Minikube** (Local Kubernetes)
   - Use `Jenkinsfile.minikube`
   - Pulls image from ECR
   - Deploys to minikube cluster

3. **Deploy to EKS** (Production)
   - Use `Jenkinsfile.eks`
   - Provisions EKS cluster
   - Deploys to AWS

---

## Summary

| Pipeline | Duration | Focus | Output |
|----------|----------|-------|--------|
| Build | 10-15 min | Lint, test | test-results.xml, coverage.xml |
| QA | 5-10 min | Coverage, security | coverage-report/ |
| Deploy | 5-10 min | Start server | app.log, running API |
| Integration Test | 5-10 min | Endpoint tests | test-reports/ |
| **Total** | **~40 min** | **Full CI/CD** | **Deployed & tested** |

All 4 pipelines working together provide a complete local development, testing, and deployment workflow for the EC2 Creator API.
