# TODO — Tomorrow's Jenkins Pipeline Work

## Status
✅ **BUILD Pipeline Complete** — Fully tested and working
⏳ **TEST, DEPLOY, VALIDATE Pipelines** — Ready to be implemented

---

## Task List for Tomorrow

### Phase 1: Implement TEST Pipeline
**File:** `jenkins/deployment/local/Jenkinsfile.test`

**Stages to implement:**
1. Unstash Workspace (from BUILD)
2. Coverage Analysis
   - Run pytest with coverage threshold (≥70%)
   - Generate HTML coverage report
3. Security Scan
   - Check for hardcoded secrets (api_key, password, token)
   - Check for unsafe SQL patterns
4. Dependency Check
   - List outdated packages
   - Report vulnerable versions

**Key Points:**
- NO checkout stage (use unstashed code)
- NO venv setup (use unstashed venv)
- NO pip install (packages already installed in BUILD)
- All tools (pytest, flake8, etc.) available in PATH from stashed venv

**Expected Output:**
- `coverage-report/index.html` (HTML coverage visualization)
- Console output with security findings
- Console output with dependency audit

**Success Criteria:**
- Coverage ≥ 70%
- No hardcoded secrets detected
- Pipeline completes without errors

---

### Phase 2: Implement DEPLOY Pipeline
**File:** `jenkins/deployment/local/Jenkinsfile.deploy`

**Stages to implement:**
1. Unstash Workspace (from BUILD)
2. Pre-Deployment Checks
   - Kill any process on port 8000
   - Verify app.main exists
3. Start Server
   - Run: `python -m uvicorn app.main:app --reload`
   - Capture PID to `/tmp/ec2-creator.pid`
   - Redirect logs to `${WORKSPACE}/app.log`
   - Run in background (nohup or &)
4. Health Check
   - Poll `http://localhost:8000/health` endpoint
   - Max 10 retries, 2 second intervals
   - Confirm response is 200 OK
5. Verify Routes
   - Test `/instances` endpoint (GET)
   - Test `/docs` endpoint (GET, Swagger UI)
   - Confirm both return 200

**Key Points:**
- NO checkout stage (use unstashed code)
- NO venv setup (use unstashed venv)
- Server runs in BACKGROUND after stage completes
- Server continues running for VALIDATE pipeline
- PID file critical for VALIDATE to find server

**Expected Output:**
- Server running on `http://localhost:8000`
- Swagger UI available on `http://localhost:8000/docs`
- `app.log` with server startup messages
- `/tmp/ec2-creator.pid` file with process ID

**Success Criteria:**
- Server starts without errors
- `/health` endpoint returns 200 OK
- `/instances` endpoint returns 200 OK
- `/docs` endpoint returns 200 OK

---

### Phase 3: Implement VALIDATE Pipeline
**File:** `jenkins/deployment/local/Jenkinsfile.validate`

**Stages to implement:**
1. Verify Server Running
   - Check `/tmp/ec2-creator.pid` file exists
   - Verify process is still alive (`ps -p <pid>`)
2. Wait for Server
   - Retry curl to `/health` endpoint
   - Max 5 retries, 2 second intervals
3. Run Integration Tests
   - Execute `test_api.py` script (already in repo)
   - Tests all major endpoints
4. Validate API Endpoints
   - GET /health (expect 200)
   - GET /instances (expect 200)
   - GET /docs (expect 200)
   - GET /openapi.json (expect 200)
5. Performance Check
   - Time `/health` endpoint response
   - Time `/instances` endpoint response
   - Report response times in console
6. Generate Report
   - Create `validation-artifacts/report.txt`
   - Summary: all tests passed, response times, status
7. Stop Server (in post block)
   - Read PID from `/tmp/ec2-creator.pid`
   - Kill server: `kill $(cat /tmp/ec2-creator.pid)`
   - Remove PID file
   - Cleanup complete ✓

**Key Points:**
- NO checkout stage (not needed)
- NO venv setup (not needed, tests don't require venv)
- Connect to ALREADY RUNNING SERVER from DEPLOY pipeline
- Must guarantee server is killed (use `post { always }` block)
- Clean exit even if tests fail

**Expected Output:**
- Integration tests pass
- All endpoints return correct status codes
- Response times logged and acceptable (< 200ms typical)
- Server killed cleanly at end
- `validation-artifacts/report.txt` generated

**Success Criteria:**
- All 5 integration tests pass
- All endpoints return correct status
- Response times reasonable
- Server successfully killed

---

### Phase 4: Enable Pipeline Triggers & Chains
**Task:** Connect all 4 pipelines into a single chain

**Steps:**
1. Edit `Jenkinsfile.build` post.success section
   - Uncomment: `build job: 'ec2-creator-test'`
   - Change job name if needed

2. Edit `Jenkinsfile.test` post.success section
   - Add: `build job: 'ec2-creator-deploy-local'`

3. Edit `Jenkinsfile.deploy` post.success section
   - Add: `build job: 'ec2-creator-validate'`

4. Test the chain
   - Start BUILD manually in Jenkins
   - Verify TEST triggers on BUILD success
   - Verify DEPLOY triggers on TEST success
   - Verify VALIDATE triggers on DEPLOY success
   - Verify server is killed after VALIDATE completes

**Expected Chain Flow:**
```
BUILD ✓ (15 min)
  ↓
TEST ✓ (10 min)
  ↓
DEPLOY ✓ (10 min, server running)
  ↓
VALIDATE ✓ (10 min, kills server)
  ↓
✓ All pipelines complete, full CI/CD cycle done
```

---

### Phase 5: Create Integration Tests
**Task:** Ensure `test_api.py` has comprehensive test coverage

**Tests to verify exist:**
1. Health check — GET /health
2. List instances — GET /instances
3. Invalid instance type — POST with invalid type (expect 400)
4. Invalid AMI — POST with invalid AMI (expect 400)
5. Swagger UI — GET /docs (expect 200)

**File:** `test_api.py` (root of project)

**Note:** File already exists in repo, verify it has all above tests.

---

### Phase 6: Documentation & Final Validation
**Tasks:**
1. Update `docs/PIPELINE_SUMMARY.md` with real timings (after running pipelines)
2. Create `docs/JENKINS_QUICK_START.md` — 5-minute guide to run full pipeline
3. Update `README.md` with links to pipeline documentation
4. Test full end-to-end flow at least once
5. Capture screenshots of Jenkins UI showing all 4 pipelines

---

## Checklist for Tomorrow

### Morning — Implement TEST Pipeline
- [ ] Review `Jenkinsfile.test` template
- [ ] Implement Unstash stage
- [ ] Implement Coverage Analysis stage
- [ ] Implement Security Scan stage
- [ ] Implement Dependency Check stage
- [ ] Test locally (if possible)
- [ ] Commit: "Implement TEST pipeline"

### Mid-Morning — Implement DEPLOY Pipeline
- [ ] Review `Jenkinsfile.deploy` template
- [ ] Implement Unstash stage
- [ ] Implement Pre-Deployment Checks stage
- [ ] Implement Start Server stage (background process)
- [ ] Implement Health Check stage (retry logic)
- [ ] Implement Verify Routes stage
- [ ] Test manually first: can uvicorn start? Can I curl /health?
- [ ] Commit: "Implement DEPLOY pipeline"

### Mid-Afternoon — Implement VALIDATE Pipeline
- [ ] Review `Jenkinsfile.validate` template
- [ ] Implement Verify Server Running stage
- [ ] Implement Wait for Server stage
- [ ] Implement Run Integration Tests stage
- [ ] Implement Validate Endpoints stage
- [ ] Implement Performance Check stage
- [ ] Implement Generate Report stage
- [ ] **CRITICAL:** Implement post block with server kill
- [ ] Test manually: run test_api.py against running server
- [ ] Commit: "Implement VALIDATE pipeline"

### Late Afternoon — Enable Chains & Test
- [ ] Enable BUILD → TEST trigger
- [ ] Enable TEST → DEPLOY trigger
- [ ] Enable DEPLOY → VALIDATE trigger
- [ ] Run full pipeline chain: BUILD → TEST → DEPLOY → VALIDATE
- [ ] Verify server killed after VALIDATE completes
- [ ] Commit: "Enable pipeline triggers and chains"

### End of Day — Documentation
- [ ] Update pipeline documentation with real times
- [ ] Create QUICK_START guide
- [ ] Test docs by following them step-by-step
- [ ] Final commit: "Documentation updates"

---

## Estimated Time

| Task | Time |
|------|------|
| TEST Pipeline | 1 hour |
| DEPLOY Pipeline | 1.5 hours |
| VALIDATE Pipeline | 1.5 hours |
| Enable chains & test | 1 hour |
| Documentation | 30 min |
| **Total** | **~5-6 hours** |

---

## Important Notes

1. **Server Cleanup is Critical**
   - VALIDATE pipeline MUST kill server in `post { always }` block
   - Don't rely on timeout or other mechanisms
   - Use explicit: `kill $(cat /tmp/ec2-creator.pid)` with error handling

2. **Port 8000 Conflicts**
   - If port 8000 is in use, DEPLOY will fail
   - Manual cleanup: `lsof -ti:8000 | xargs kill -9`
   - DEPLOY pipeline includes pre-check to kill old processes

3. **Test File Location**
   - `test_api.py` should be in root of project
   - Should NOT be in `tests/` directory
   - VALIDATE will run it directly

4. **No New Tests Needed in BUILD**
   - Tests directory can remain empty (0 tests found)
   - Integration tests happen in VALIDATE against running server
   - This is a valid pattern for microservices

5. **Stash/Unstash Files Are Large**
   - BUILD stashes 9660 files (~200 MB estimated)
   - Unstash happens at start of TEST, DEPLOY
   - This is normal and expected

---

## Success Looks Like

At end of day tomorrow:

```
BUILD ✓
├─ Checkout
├─ Venv Setup
├─ Install Dependencies
├─ Lint
├─ Unit Tests
└─ Stash Workspace → triggers TEST

TEST ✓
├─ Unstash Workspace
├─ Coverage Analysis
├─ Security Scan
├─ Dependency Check
└─ → triggers DEPLOY

DEPLOY ✓
├─ Unstash Workspace
├─ Pre-Deployment Checks
├─ Start Server (running on :8000)
├─ Health Check
├─ Verify Routes
└─ → triggers VALIDATE

VALIDATE ✓
├─ Verify Server Running
├─ Wait for Server
├─ Run Integration Tests
├─ Validate API Endpoints
├─ Performance Check
├─ Generate Report
└─ Stop Server ← CLEANUP COMPLETE

Full CI/CD cycle: ~40-45 minutes, zero manual intervention
```

---

## Questions to Revisit

1. Should we add Slack notifications on pipeline success/failure?
2. Should we archive coverage HTML reports in Jenkins?
3. Should VALIDATE generate a detailed HTML report instead of .txt?
4. After this works, should we create Docker, Minikube, EKS pipeline versions?

---

## Git Commit Strategy Tomorrow

Commit frequently to maintain clear history:

```bash
git commit -m "Implement TEST pipeline"
git commit -m "Implement DEPLOY pipeline"
git commit -m "Implement VALIDATE pipeline"
git commit -m "Enable pipeline triggers and chains"
git commit -m "Documentation updates for full CI/CD"
```

Each commit should be atomic and buildable.

---

Good luck tomorrow! 🚀

