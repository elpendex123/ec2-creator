# Local Deployment Pipelines — Consolidated Build, Test, Deploy, Validate

Complete guide to the 4-stage local CI/CD pipeline for the EC2 Creator API.

---

## Overview: 15 Steps, 4 Pipelines, Zero Duplication

```
PIPELINE 1: BUILD          PIPELINE 2: TEST           PIPELINE 3: DEPLOY        PIPELINE 4: VALIDATE
(10-15 min)               (5-10 min)                (5-10 min)               (5-10 min)
┌────────────────────┐    ┌────────────────────┐    ┌────────────────────┐    ┌────────────────────┐
│ 1. Checkout        │    │ 6. Coverage        │    │ 9. Start Server    │    │ 12. Run Tests      │
│ 2. Venv Setup      │───→│ 7. Security Scan   │───→│10. Health Check    │───→│13. Validate API    │
│ 3. Install Deps    │    │ 8. Dep Check       │    │11. Verify Routes   │    │14. Performance     │
│ 4. Lint            │    │                    │    │                    │    │15. Archive Results │
│ 5. Unit Tests      │    │ (unstashes workspace)    │ (unstashes workspace)    │ (no unstash needed)│
│                    │    │                    │    │ (starts server)    │    │ (connects to running│
│ (stashes workspace)│    │ (triggers next)    │    │ (triggers next)    │    │  server, kills it) │
└────────────────────┘    └────────────────────┘    └────────────────────┘    └────────────────────┘
```

**Key benefit:** Venv is installed ONCE in BUILD, then reused in TEST and DEPLOY via stash/unstash. No repeated work.

---

## Pipeline 1: BUILD

**File:** `jenkins/deployment/local/Jenkinsfile.build`

**Purpose:** Initialize environment, lint code, run unit tests

**Stages:**
1. **Checkout** — Clone repository
2. **Venv Setup** — Create Python virtual environment with Python 3.11
3. **Install Dependencies** — Install packages from `requirements.txt`
4. **Lint** — Run flake8 on `app/` directory (max-line-length=120)
5. **Unit Tests** — Run pytest with coverage reporting
6. **Stash Workspace** — Save venv + source for downstream pipelines

**Key Features:**
- Creates fresh virtual environment
- Generates coverage HTML report
- Archives test results (test-results.xml, coverage.xml)
- Stashes entire workspace including venv
- **Auto-triggers TEST pipeline on success**

**Configuration:**
- Timeout: 15 minutes
- Keep last: 10 builds
- Environment: `VENV_DIR = ${WORKSPACE}/venv`

**Success Criteria:**
✓ Code passes flake8 (no style violations)
✓ All unit tests pass
✓ Stash completes without errors

---

## Pipeline 2: TEST

**File:** `jenkins/deployment/local/Jenkinsfile.test`

**Purpose:** Code quality analysis, security scanning, dependency checks

**Stages:**
1. **Unstash Workspace** — Restore venv + source from BUILD (no checkout, no pip install)
2. **Coverage Analysis** — Run pytest with coverage, enforce ≥ 70% threshold
3. **Security Scan** — Check for hardcoded secrets, unsafe SQL patterns
4. **Dependency Check** — List outdated packages and vulnerabilities
5. **Archive Test Reports** — Save coverage report for HTML display

**Key Features:**
- NO checkout (uses unstashed source)
- NO venv recreation (uses unstashed venv)
- NO pip install (uses unstashed packages)
- Enforces 70% code coverage minimum
- Basic pattern matching for security issues
- **Auto-triggers DEPLOY pipeline on success**

**Configuration:**
- Timeout: 10 minutes
- Keep last: 10 builds
- Coverage threshold: ≥ 70%

**Success Criteria:**
✓ Coverage ≥ 70%
✓ No hardcoded secrets detected
✓ No unsafe patterns found

---

## Pipeline 3: DEPLOY

**File:** `jenkins/deployment/local/Jenkinsfile.deploy`

**Purpose:** Start FastAPI server, verify it's running

**Stages:**
1. **Unstash Workspace** — Restore venv + source from BUILD
2. **Pre-Deployment Checks** — Kill existing process on port 8000, verify app files exist
3. **Start Server** — Launch uvicorn in background, save PID to `/tmp/ec2-creator.pid`
4. **Health Check** — Poll `/health` endpoint (max 10 retries, 2s intervals)
5. **Verify Routes** — Test `/instances` and `/docs` endpoints
6. **Deployment Summary** — Print API details (URL, Swagger UI link, PID file location)

**Key Features:**
- NO checkout (uses unstashed source)
- NO venv recreation (uses unstashed venv)
- Kills any existing process on port 8000
- Saves server PID to `/tmp/ec2-creator.pid` for VALIDATE to use
- Server continues running after pipeline completes
- Server logs written to `${WORKSPACE}/app.log`
- **Auto-triggers VALIDATE pipeline on success**

**Configuration:**
- Timeout: 15 minutes
- Keep last: 5 builds
- API Port: 8000
- API Host: localhost
- PID File: `/tmp/ec2-creator.pid`

**Server Details After Success:**
```
API URL: http://localhost:8000
Swagger UI: http://localhost:8000/docs
ReDoc: http://localhost:8000/redoc
PID File: /tmp/ec2-creator.pid
Log File: ${WORKSPACE}/app.log
```

**Success Criteria:**
✓ Port 8000 is available (or old process killed)
✓ Server starts without errors
✓ `/health` endpoint responds 200 OK
✓ `/instances` endpoint is accessible
✓ Swagger UI loads (returns 200)

---

## Pipeline 4: VALIDATE

**File:** `jenkins/deployment/local/Jenkinsfile.validate`

**Purpose:** Run integration tests against running server

**Stages:**
1. **Verify Server Running** — Check PID file exists and process is alive
2. **Wait for Server** — Retry connecting to API (max 5 retries, 2s intervals)
3. **Run Integration Tests** — Execute `test_api.py` script
4. **Validate API Endpoints** — Test `/health`, `/instances`, `/openapi.json`, `/docs`
5. **Performance Check** — Time responses from key endpoints
6. **Generate Validation Report** — Create summary document
7. **Stop Server** — Kill server process and clean up PID file

**Key Features:**
- NO checkout (not needed)
- NO venv (tests don't require it, uses Python 3 directly)
- Connects to already-running server from DEPLOY pipeline
- Reads PID from `/tmp/ec2-creator.pid`
- Validates all major endpoints
- Measures response times
- Kills server in `post { always }` block (guaranteed cleanup)

**Configuration:**
- Timeout: 10 minutes
- Keep last: 10 builds
- API URL: `http://localhost:8000`

**Integration Tests Run (from test_api.py):**
1. Health check — GET /health
2. List instances — GET /instances
3. Invalid instance type — POST with t2.large (expects 400)
4. Invalid AMI — POST with invalid AMI (expects 400)
5. Swagger UI — GET /docs (expects 200)

**Success Criteria:**
✓ Server process is running
✓ All 5 integration tests pass
✓ All endpoints respond with correct status codes
✓ Response times are reasonable
✓ Server is killed cleanly at end

---

## Complete Workflow Example

### Starting a Full Pipeline Chain

**Option 1: Jenkins UI**
```
1. Go to http://jenkins:8080/job/ec2-creator-build
2. Click "Build Now"
3. Wait for all 4 pipelines to complete
```

**Option 2: curl**
```bash
curl -X POST http://jenkins:8080/job/ec2-creator-build/build \
  -u username:token
```

### Pipeline Execution Timeline

```
Time    Stage                                   Status
────────────────────────────────────────────────────────
0:00    BUILD: Checkout                         [RUNNING]
0:05    BUILD: Venv + Install                  [RUNNING]
0:10    BUILD: Lint                            [RUNNING]
0:12    BUILD: Unit Tests                      [RUNNING]
0:15    ✓ BUILD complete                       [SUCCESS]
        → Stash workspace
        → Trigger TEST
────────────────────────────────────────────────────────
0:16    TEST: Unstash                          [RUNNING]
0:17    TEST: Coverage                         [RUNNING]
0:20    TEST: Security + Dependencies          [RUNNING]
0:23    ✓ TEST complete                        [SUCCESS]
        → Trigger DEPLOY
────────────────────────────────────────────────────────
0:24    DEPLOY: Unstash                        [RUNNING]
0:25    DEPLOY: Pre-checks + Start Server      [RUNNING]
0:28    DEPLOY: Health check + Routes          [RUNNING]
0:32    ✓ DEPLOY complete                      [SUCCESS]
        → Server running on localhost:8000
        → Trigger VALIDATE
────────────────────────────────────────────────────────
0:33    VALIDATE: Verify Server                [RUNNING]
0:35    VALIDATE: Integration Tests            [RUNNING]
0:38    VALIDATE: API Validation + Performance [RUNNING]
0:40    ✓ VALIDATE complete                    [SUCCESS]
        → Kill server
────────────────────────────────────────────────────────
Total time: ~40 minutes from start to finish
```

---

## Artifact Locations

### BUILD Pipeline
```
build-artifacts/
  ├── test-results.xml         # JUnit format
  └── coverage.xml             # Cobertura format
```

### TEST Pipeline
```
coverage-report/               # Published HTML report
  ├── index.html
  ├── status.json
  └── ...
```

### DEPLOY Pipeline
```
${WORKSPACE}/
  ├── app.log                  # Server output
  └── venv/                    # Python environment (stashed)

/tmp/ec2-creator.pid           # Server process ID
```

### VALIDATE Pipeline
```
validation-artifacts/
  └── report.txt               # Test summary
```

---

## Triggering Pipelines Manually (Skipping Earlier Stages)

**Note:** This only works if earlier pipelines have already run and workspace is stashed.

### Run TEST only (requires BUILD artifacts)
```bash
curl -X POST http://jenkins:8080/job/ec2-creator-test/build -u user:token
```

### Run DEPLOY only (requires BUILD artifacts)
```bash
curl -X POST http://jenkins:8080/job/ec2-creator-deploy-local/build -u user:token
```

### Run VALIDATE only (requires running server)
```bash
# First, ensure DEPLOY pipeline has run and server is still running
curl -X POST http://jenkins:8080/job/ec2-creator-validate/build -u user:token
```

---

## Troubleshooting

### BUILD Pipeline Fails at "Unit Tests"

**Cause:** Tests directory missing or no test files

**Fix:**
```bash
mkdir -p tests
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

### TEST Pipeline Fails at "Unstash"

**Cause:** BUILD pipeline didn't complete or stash failed

**Fix:** Re-run BUILD pipeline

```bash
curl -X POST http://jenkins:8080/job/ec2-creator-build/build -u user:token
```

### DEPLOY Pipeline Fails at "Health Check"

**Cause:** Server didn't start, or dependencies missing

**Fix:**
1. Check server logs: `tail -50 ${WORKSPACE}/app.log`
2. Check if uvicorn is installed: `which uvicorn`
3. Manually start server to debug:
```bash
source venv/bin/activate
python -m uvicorn app.main:app --reload
```

### VALIDATE Pipeline Fails at "Verify Server Running"

**Cause:** PID file doesn't exist or process was killed

**Fix:**
1. Check if DEPLOY pipeline completed successfully
2. Check if server is still running:
```bash
ps aux | grep uvicorn
```
3. Re-run DEPLOY pipeline:
```bash
curl -X POST http://jenkins:8080/job/ec2-creator-deploy-local/build -u user:token
```

### Port 8000 Still in Use

**Manual cleanup:**
```bash
lsof -ti:8000 | xargs kill -9
```

---

## Manual Testing Without Jenkins

To run all 4 stages manually:

```bash
# Stage 1: BUILD
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
flake8 app/ --max-line-length=120
pytest tests/ -v --cov=app --cov-report=html

# Stage 2: TEST
# (venv already active)
pytest tests/ --cov=app --cov-fail-under=70

# Stage 3: DEPLOY
# (venv already active)
python -m uvicorn app.main:app --reload &
sleep 3
curl http://localhost:8000/health

# Stage 4: VALIDATE
# (in new terminal, or after starting server in background)
python3 test_api.py

# Cleanup
kill %1  # kill background uvicorn
```

---

## Next Steps

Once all 4 pipelines pass:

1. **Deploy to Docker** — Use `Jenkinsfile.docker` to build image and push to ECR
2. **Deploy to Minikube** — Use `Jenkinsfile.minikube` to test on local Kubernetes
3. **Deploy to EKS** — Use `Jenkinsfile.eks` for production on AWS

---

## Summary Table

| Pipeline | Duration | What It Does | Workspace | Output |
|----------|----------|--------------|-----------|--------|
| BUILD | 10-15 min | Lint, test, stash | Creates + stashes | test-results.xml, coverage.xml |
| TEST | 5-10 min | Coverage, security, deps | Unstashes (reuses) | coverage-report/ |
| DEPLOY | 5-10 min | Start server, health check | Unstashes (reuses) | app.log, /tmp/ec2-creator.pid |
| VALIDATE | 5-10 min | Integration tests, performance | Connects to running server | validation report, kills server |
| **Total** | **~40 min** | **Full CI/CD cycle** | **Efficient reuse** | **Fully tested & deployed** |

No stage repeats work from earlier stages. Each pipeline has a single, focused responsibility.
