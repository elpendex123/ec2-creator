# Jenkins BUILD Pipeline — Troubleshooting & Issues Resolved

## Overview
Complete record of all issues encountered while setting up the consolidated BUILD pipeline (`Jenkinsfile.build`) and the solutions implemented. This document serves as a reference for future troubleshooting.

---

## Issues Encountered & Resolved

### Issue 1: Duplicate Stages Across Pipelines
**Problem:** All 4 pipelines (BUILD, TEST, DEPLOY, VALIDATE) had identical checkout, venv setup, and pip install stages, causing massive duplication of work.

**Root Cause:** Initial design didn't leverage Jenkins stash/unstash feature.

**Solution:**
- Consolidate all checkout/venv/pip into BUILD pipeline only
- Implement Jenkins `stash` at end of BUILD pipeline to save workspace
- Have downstream pipelines (TEST, DEPLOY, VALIDATE) `unstash` instead of recreating
- Result: 12+ repeated stages → 1 occurrence only ✓

**Commits:**
- `jenkins/deployment/local/Jenkinsfile.build` — Initial consolidation
- `jenkins/deployment/local/Jenkinsfile.test` — Changed to unstash pattern

---

### Issue 2: Slow Builds — Reinstalling Dependencies Every Time
**Problem:** Each build was taking 5-10 minutes installing dependencies, even when requirements.txt hadn't changed.

**Root Cause:** No caching mechanism. pip always runs, even if packages already installed.

**Solution:**
- Implement SHA256 hash checking of `requirements.txt`
- Store hash in `${VENV_DIR}/.requirements.hash`
- Before running pip install, check if:
  1. Hash file exists
  2. Hash matches current requirements.txt
  3. If both true → skip pip install
- Added validation: Check if flake8 binary exists before trusting hash cache (prevents "not found" errors)

**Code Pattern:**
```bash
CURRENT_HASH=$(sha256sum requirements.txt | awk '{print $1}')
HASH_FILE="${VENV_DIR}/.requirements.hash"

if [ -f "$HASH_FILE" ] && which flake8 > /dev/null 2>&1; then
    PREVIOUS_HASH=$(cat "$HASH_FILE")
    if [ "$CURRENT_HASH" = "$PREVIOUS_HASH" ]; then
        echo "✓ requirements.txt unchanged and packages present, skipping pip install"
        exit 0
    fi
fi
```

**Performance Impact:**
- First build: ~60 seconds (download + install all packages)
- Subsequent builds: ~10 seconds (hash match, skip pip install) ✓

**Commits:**
- `jenkins/deployment/local/Jenkinsfile.build` — Initial hash implementation
- `1c20a51` — "Fix: validate packages exist before skipping pip install"

---

### Issue 3: Flake8 "Command Not Found" (Exit Code 127)
**Problem:** Lint stage failed with: `line 5: flake8: command not found`

**Root Causes (Multiple):**
1. Tools were installing to `~/.local/bin` (user site-packages) instead of venv
2. Venv activation with `. "${VENV_DIR}/bin/activate"` failed in Jenkins heredoc context
3. Workspace path contains spaces: `/var/lib/jenkins/workspace/EC2-Creator/Local/1 Build` — shell splitting on spaces

**Solutions Applied (in order):**
1. **Add `--no-user` flag to pip install**
   ```bash
   pip install --no-user -r requirements.txt
   ```
   Forces pip to use venv, not user site-packages ✓

2. **Replace venv sourcing with PATH export**
   - ❌ Old: `. "${VENV_DIR}/bin/activate"` (fails in heredoc with spaces in path)
   - ✅ New: `export PATH="${VENV_DIR}/bin:$PATH"` (simpler, more reliable)
   - Add `#!/bin/bash` shebang to all heredocs for explicit shell type

3. **Quote all variable expansions**
   - ❌ Old: `${VENV_DIR}/bin/flake8` (splits on space in path)
   - ✅ New: `"${VENV_DIR}/bin/flake8"` (protects path with spaces)

**Code Fix:**
```bash
sh '''#!/bin/bash
    set -e
    export PATH="${VENV_DIR}/bin:$PATH"
    echo "=== Running flake8 linter ==="
    flake8 app/ --max-line-length=120
    echo "✓ Linting passed"
'''
```

**Commits:**
- `d06ef69` — "Simplify venv activation: use PATH export instead of source command"

---

### Issue 4: Hash File Write Failed — Directory Nonexistent
**Problem:** mkdir created venv dir after hash file write attempted → permission/ordering error.

**Root Cause:** Logic was: write hash → mkdir. Should be: mkdir → write hash.

**Solution:**
```bash
mkdir -p "${VENV_DIR}"  # Create dir first
echo "$CURRENT_HASH" > "${HASH_FILE}"  # Then write hash
```

**Commit:**
- `jenkins/deployment/local/Jenkinsfile.build` — Reordered mkdir before hash write

---

### Issue 5: Flake8 Linting Violations (7 Total)
**Problem:** Build passed venv/deps but failed on Lint stage. Flake8 found 7 violations:

**Violations Found:**
1. `app/routers/instances.py:41:121` — Line too long (E501, 165 > 120 chars)
2. `app/services/aws_cli.py:97:9` — Unused variable `result` (F841)
3. `app/services/aws_cli.py:102:9` — Unused variable `result` (F841)
4. `app/services/aws_cli.py:107:9` — Unused variable `result` (F841)
5. `app/services/db.py:55:121` — Line too long (E501, 132 > 120 chars)
6. `app/services/terraform.py:100:9` — Unused variable `result` (F841)
7. `app/services/terraform.py:105:9` — Unused variable `result` (F841)
8. `app/services/terraform.py:110:9` — Unused variable `result` (F841)

**Solutions Applied:**

1. **Break long error message** in `instances.py:41`
   ```python
   # Before (165 chars):
   detail=f"Instance type '{request.instance_type}' or AMI '{request.ami}' not allowed. Only t3.micro and t4g.micro instance types are free tier eligible."

   # After (3 lines):
   detail=(
       f"Instance type '{request.instance_type}' or AMI '{request.ami}' "
       "not allowed. Only t3.micro and t4g.micro instance types are "
       "free tier eligible."
   )
   ```

2. **Remove unused `result` variables** in `aws_cli.py`
   ```python
   # Before:
   def start(self, instance_id: str) -> Dict[str, str]:
       result = self._run_script("start_instance.sh", [instance_id])
       return {"state": "running", "id": instance_id}

   # After:
   def start(self, instance_id: str) -> Dict[str, str]:
       self._run_script("start_instance.sh", [instance_id])
       return {"state": "running", "id": instance_id}
   ```

3. **Break long SQL statement** in `db.py:55`
   ```python
   # Before (132 chars):
   INSERT INTO instances (id, name, public_ip, ami, instance_type, state, ssh_string, backend_used, created_at, updated_at)

   # After (split across 2 lines):
   INSERT INTO instances
   (id, name, public_ip, ami, instance_type, state, ssh_string,
    backend_used, created_at, updated_at)
   ```

4. **Remove unused `result` variables** in `terraform.py` (same as aws_cli.py)

**Commit:**
- `b3ef87b` — "Fix: resolve flake8 linting violations"

---

### Issue 6: Missing pytest-cov Plugin
**Problem:** Unit Tests stage showed warning: `pytest: error: unrecognized arguments: --cov=app --cov-report=html`

**Root Cause:** `pytest-cov` package not in requirements.txt, so `--cov` flags weren't recognized.

**Solution:** Add pytest-cov to requirements.txt
```
pytest
pytest-cov  # ← Added
httpx
```

**Result:** Coverage reporting now works ✓

**Commit:**
- `22feeb0` — "Add pytest-cov and disable TEST trigger temporarily"

---

### Issue 7: Missing Downstream Pipeline Jobs
**Problem:** BUILD pipeline tried to trigger `ec2-creator-test` job on success, but job doesn't exist yet.

**Error:**
```
hudson.AbortException: No item named ec2-creator-test found
```

**Solution:** Comment out the trigger until TEST, DEPLOY, VALIDATE jobs are created
```groovy
success {
    script {
        echo "✓ BUILD complete"
        // TODO: Trigger TEST pipeline once ec2-creator-test job is created
        // build job: 'ec2-creator-test', wait: true, propagate: false
    }
}
```

**Commit:**
- `22feeb0` — "Add pytest-cov and disable TEST trigger temporarily"

---

## Final BUILD Pipeline Status

✅ **BUILD Pipeline: FULLY FUNCTIONAL**

All stages passing:
1. ✓ Checkout — Code cloned from GitHub
2. ✓ Venv Setup — Python 3.10 environment created
3. ✓ Install Dependencies — 37 packages installed (with hash caching)
4. ✓ Lint — Flake8 passed (all violations fixed)
5. ✓ Unit Tests — Pytest runs with coverage support
6. ✓ Stash Workspace — 9660 files saved for downstream pipelines

**Performance:**
- First build: ~60 seconds
- Subsequent builds (with caching): ~10 seconds ⚡

**Workspace artifacts created:**
- `test-results.xml` (JUnit format)
- `build-artifacts/test-results.xml` (archived copy)
- Entire venv stashed for reuse

---

## Commits Made Today

1. `1c20a51` — Fix: validate packages exist before skipping pip install
2. `b3ef87b` — Fix: resolve flake8 linting violations (7 violations)
3. `22feeb0` — Add pytest-cov and disable TEST trigger temporarily

---

## Key Learnings

### 1. Jenkins Heredoc Shell Execution
- Always use `#!/bin/bash` shebang in heredocs for consistent shell behavior
- Quote all variable expansions: `"${VAR}"` not `${VAR}`
- Avoid sourcing activate scripts; use PATH export instead
- Workspace paths with spaces require careful quoting

### 2. Venv Activation Patterns
**Better pattern for Jenkins:**
```bash
export PATH="${VENV_DIR}/bin:$PATH"
flake8 app/
```

**Avoid in Jenkins heredoc:**
```bash
. "${VENV_DIR}/bin/activate"  # Can fail with spaces in path
```

### 3. Dependency Caching
Hash-based caching dramatically improves build times:
- Store hash of requirements.txt
- Check hash + binary existence before skipping pip install
- Protects against edge cases (venv cleared, but hash lingers)

### 4. Pipeline Architecture
Jenkins stash/unstash is powerful for multi-stage pipelines:
- Checkout once in BUILD
- Install deps once in BUILD
- Reuse in TEST, DEPLOY, VALIDATE via unstash
- No repeated work across 4 pipelines ✓

---

## What's Next (Tomorrow's Tasks)

See `JENKINS_BUILD_TOMORROW.md` for detailed TODO list of remaining work:

1. **Create TEST pipeline** — Unstash → Coverage analysis → Security scan → Dep check
2. **Create DEPLOY pipeline** — Unstash → Start server → Health check → Verify routes
3. **Create VALIDATE pipeline** — Connect to server → Integration tests → Performance check → Cleanup
4. **Enable pipeline triggers** — BUILD → TEST → DEPLOY → VALIDATE chain
5. **Create integration tests** — Tests for /health, /instances, /docs endpoints
6. **Document full workflow** — End-to-end guide for users

---

## References

- **BUILD Pipeline File:** `jenkins/deployment/local/Jenkinsfile.build`
- **Pipeline Documentation:** `docs/JENKINS_LOCAL_PIPELINES.md`
- **Quick Reference:** `docs/PIPELINE_SUMMARY.md`
- **Git Repo:** https://github.com/elpendex123/ec2-creator

