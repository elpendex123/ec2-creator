# Jenkins Local Pipelines — Quick Reference

## The 4 Consolidated Pipelines (No Duplication)

```
BUILD (10-15m)      TEST (5-10m)        DEPLOY (5-10m)       VALIDATE (5-10m)
┌────────────────┐  ┌────────────────┐  ┌────────────────┐    ┌────────────────┐
│ 1. Checkout    │  │ 6. Coverage    │  │ 9. Start       │    │12. Run Tests   │
│ 2. Venv Setup  │→ │ 7. Security    │→ │10. Health      │───→│13. Validate API│
│ 3. Install     │  │ 8. Dep Check   │  │11. Routes      │    │14. Performance │
│ 4. Lint        │  │                │  │                │    │15. Archive     │
│ 5. Unit Tests  │  │ (unstashes)    │  │ (unstashes)    │    │(kills server)  │
│                │  │ (no checkout)  │  │ (no checkout)  │    │                │
│ (stashes)      │  │ (no pip)       │  │ (server runs)  │    │(connects to    │
└────────────────┘  └────────────────┘  └────────────────┘    │running server) │
                                                               └────────────────┘
```

**Key:** Venv created once, reused 3 times. No repeated work.

---

## Pipeline 1: BUILD
**File:** `jenkins/deployment/local/Jenkinsfile.build`

**Does:**
- Checkout code
- Setup Python 3.11 venv
- Install dependencies (requirements.txt)
- Lint code (flake8)
- Run unit tests (pytest + coverage)
- Stash workspace for next pipelines

**Output:**
- test-results.xml
- coverage.xml
- htmlcov/ (coverage HTML)

**Triggers:** TEST on success

---

## Pipeline 2: TEST
**File:** `jenkins/deployment/local/Jenkinsfile.test`

**Does:**
- **Unstash workspace from BUILD** (no checkout, no venv recreation, no pip install)
- Coverage analysis (enforce ≥70%)
- Security scanning (hardcoded secrets check)
- Dependency check (outdated packages)

**Key Difference:** No duplicate stages from BUILD

**Output:**
- coverage-report/ (HTML report)

**Triggers:** DEPLOY on success

---

## Pipeline 3: DEPLOY
**File:** `jenkins/deployment/local/Jenkinsfile.deploy`

**Does:**
- **Unstash workspace from BUILD** (no checkout, no venv recreation, no pip install)
- Pre-checks (kill existing process on port 8000)
- Start FastAPI server on localhost:8000
- Health check (poll /health, retry 10x)
- Verify routes (/instances, /docs)

**Key Difference:** No duplicate stages from BUILD, server keeps running

**Server Info:**
- URL: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- PID saved to: /tmp/ec2-creator.pid
- Logs: ${WORKSPACE}/app.log

**Triggers:** VALIDATE on success

---

## Pipeline 4: VALIDATE
**File:** `jenkins/deployment/local/Jenkinsfile.validate`

**Does:**
- Verify server is running (check PID file)
- Wait for server (retry 5x)
- Run integration tests (test_api.py)
- Validate endpoints (/health, /instances, /docs, /openapi.json)
- Performance check (time key endpoints)
- Archive results
- **Kill server** (cleanup in post block)

**Key Difference:** Connects to already-running server, doesn't start its own

**Tests Run:**
1. Health check
2. List instances
3. Invalid instance type (expects 400)
4. Invalid AMI (expects 400)
5. Swagger UI availability

---

## How to Use

### Start Full Pipeline Chain

**Jenkins UI:**
```
1. Go to: http://jenkins:8080/job/ec2-creator-build
2. Click "Build Now"
3. All 4 pipelines run in sequence
```

**Or with curl:**
```bash
curl -X POST http://jenkins:8080/job/ec2-creator-build/build \
  -u username:token
```

### Timeline

```
0:00  BUILD starts
0:15  ✓ BUILD done → stash → trigger TEST
0:25  ✓ TEST done → trigger DEPLOY
0:35  ✓ DEPLOY done (server running) → trigger VALIDATE
0:40  ✓ VALIDATE done (server killed) → ALL DONE
```

**Total:** ~40 minutes

---

## Why This Design is Better

**Before (4 separate pipelines with duplication):**
- Checkout: 4 times
- Venv setup: 4 times
- Install deps: 4 times
- = **Wasted time & disk space**

**Now (consolidated with stash/unstash):**
- Checkout: 1 time (in BUILD)
- Venv setup: 1 time (in BUILD)
- Install deps: 1 time (in BUILD)
- Reused by TEST, DEPLOY via `unstash`
- = **Efficient, fast, clean**

---

## Artifact Locations

| Pipeline | Artifacts |
|----------|-----------|
| **BUILD** | build-artifacts/{test-results.xml, coverage.xml}, htmlcov/ |
| **TEST** | coverage-report/index.html |
| **DEPLOY** | app.log, /tmp/ec2-creator.pid |
| **VALIDATE** | validation-artifacts/report.txt |

---

## Success Indicators

### All Green ✓
```
BUILD ✓ → TEST ✓ → DEPLOY ✓ → VALIDATE ✓
API running: http://localhost:8000
All tests passed!
```

### BUILD Failed ✗
```
BUILD ✗ (linting or unit test failed)
→ Stop here. Fix code, retry BUILD.
```

### TEST Failed ✗
```
BUILD ✓ → TEST ✗ (coverage < 70% or security issue)
→ Stop here. Add more tests or fix security issues, retry TEST.
```

### DEPLOY Failed ✗
```
BUILD ✓ → TEST ✓ → DEPLOY ✗ (port in use or server crash)
→ Stop here. Kill port 8000: lsof -ti:8000 | xargs kill -9
→ Retry DEPLOY.
```

### VALIDATE Failed ✗
```
BUILD ✓ → TEST ✓ → DEPLOY ✓ → VALIDATE ✗ (test failures)
→ API still running at http://localhost:8000
→ Check logs: tail app.log
→ Fix API, retry from BUILD.
```

---

## Quick Troubleshooting

| Problem | Fix |
|---------|-----|
| Port 8000 in use | `lsof -ti:8000 \| xargs kill -9` |
| Build fails on tests | Create `tests/test_health.py` with basic test |
| Coverage too low | Add more unit tests to `tests/` |
| Server won't start | `tail app.log` to see error |
| VALIDATE can't find PID file | Re-run DEPLOY pipeline |

---

## Manual Run (No Jenkins)

```bash
# BUILD stage
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
flake8 app/ --max-line-length=120
pytest tests/ -v --cov=app --cov-report=html

# TEST stage (venv already active)
pytest tests/ --cov=app --cov-fail-under=70
python3 -c "grep -r 'api_key\|password\|secret' app/" || true

# DEPLOY stage (start server in background)
python -m uvicorn app.main:app --reload &
sleep 3
curl http://localhost:8000/health

# VALIDATE stage (in another terminal)
python3 test_api.py

# Cleanup
kill %1
```

---

## Jenkins Job Names

- `ec2-creator-build` — Pipeline 1 (BUILD)
- `ec2-creator-test` — Pipeline 2 (TEST)
- `ec2-creator-deploy-local` — Pipeline 3 (DEPLOY)
- `ec2-creator-validate` — Pipeline 4 (VALIDATE)

---

## Configuration

| Setting | Value |
|---------|-------|
| Python version | 3.11 |
| Venv location | ${WORKSPACE}/venv |
| API host | localhost |
| API port | 8000 |
| PID file | /tmp/ec2-creator.pid |
| Coverage threshold | 70% |
| Max retries (health check) | 10 |
| Max retries (VALIDATE wait) | 5 |

---

## Next Steps After Success

Once all 4 pipelines pass:

1. **Deploy to Docker** — `Jenkinsfile.docker` (build image, push to ECR)
2. **Deploy to Minikube** — `Jenkinsfile.minikube` (test on local k8s)
3. **Deploy to EKS** — `Jenkinsfile.eks` (production on AWS)

---

## See Also

- Full details: `docs/JENKINS_LOCAL_PIPELINES.md`
- Project docs: `docs/`
