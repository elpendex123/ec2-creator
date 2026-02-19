# EC2 Provisioner — Changelog

All notable changes to the EC2 Provisioner API are documented here.

## [2.0] — February 18-19, 2026

### Major Updates

#### Code Fixes
- **Fixed free-tier validation:** Updated `ALLOWED_INSTANCE_TYPES` from `["t2.micro", "t3.micro"]` to `["t3.micro", "t4g.micro"]`
  - Reason: AWS reports t2.micro as NOT free-tier eligible in most regions
  - Impact: Only t3.micro and t4g.micro instances can now be created
  - Ref: `app/config.py:32`

- **Fixed AMI validation:** Added `ami-026992d753d5622bc` (current Amazon Linux 2) to free-tier whitelist
  - Reason: Old AMI was outdated, new one is current as of Feb 2026
  - Impact: Current Amazon Linux 2 instances can now be provisioned
  - Ref: `app/config.py:38`

- **Fixed stdout pollution:** Redirected "Waiting for public IP..." message to stderr in `create_instance.sh`
  - Reason: Message was polluting stdout, breaking instance ID parsing
  - Impact: Instance IDs are now clean without embedded status messages
  - Ref: `aws_cli_bash_scripts/create_instance.sh:23`

- **Fixed response models:** Made `public_ip` and `ssh_string` Optional fields in `InstanceResponse`
  - Reason: Fields could be empty/None but model required strings
  - Impact: Responses are now valid Pydantic models in all cases
  - Ref: `app/models/instance.py:16-17`

- **Added defensive parsing:** Instance ID parsing now strips newlines and takes last line
  - Reason: Defense against future stdout pollution
  - Impact: Parser is more robust to edge cases
  - Ref: `app/routers/instances.py:58`

#### SSH Key Pair Support
- **Added SSH key configuration:** All instances now created with `my_ec2_keypair`
  - AWS CLI backend: `--key-name my_ec2_keypair` added to `run-instances` command
  - Terraform backend: `key_name` variable added and passed to aws_instance resource
  - Impact: SSH access now works out-of-the-box: `ssh -i ~/.ssh/my_ec2_keypair.pem ec2-user@<ip>`
  - Files updated:
    - `aws_cli_bash_scripts/create_instance.sh:14`
    - `terraform_bash_scripts/tf_create.sh:17`
    - `terraform/ec2/main.tf:19`
    - `terraform/ec2/variables.tf:24-27`

#### Error Messages
- **Updated validation error message:** Now shows correct instance types
  - Old: "Only t2.micro and t3.micro are free tier eligible"
  - New: "Only t3.micro and t4g.micro instance types are free tier eligible"
  - Ref: `app/routers/instances.py:41`

### Documentation (New)
- **Created `docs/` directory** with comprehensive documentation
  - `QUICK_START.md` — 5-minute quick start guide (167 lines)
  - `SSH_SETUP.md` — SSH configuration and troubleshooting (229 lines)
  - `API_REFERENCE.md` — Complete API endpoint documentation (407 lines)
  - `DEPLOYMENT.md` — Stage-by-stage deployment guide (424 lines)
  - `CHANGELOG.md` — This file

- **Updated `README.md`** (root)
  - Project overview with links to all docs
  - Quick start section
  - Feature highlight summary
  - Troubleshooting links
  - Development section
  - Project structure reference

### Testing & Verification
- ✅ Created instance with t3.micro (free-tier eligible)
- ✅ Instance creation returned clean instance ID (no status message prefix)
- ✅ SSH access works: `ssh -i ~/.ssh/my_ec2_keypair.pem ec2-user@<ip>`
- ✅ Email notifications sent successfully
- ✅ List instances endpoint works correctly
- ✅ Get instance details endpoint works correctly
- ✅ Start/stop instance endpoints work correctly
- ✅ Validation rejects invalid instance types with correct error message
- ✅ Free-tier AMI validation works for whitelisted AMIs

### Files Modified
| File | Changes |
|------|---------|
| `app/config.py` | Updated ALLOWED_INSTANCE_TYPES and FREE_TIER_AMIS |
| `app/models/instance.py` | Made public_ip and ssh_string Optional |
| `app/routers/instances.py` | Updated error message, added defensive parsing |
| `aws_cli_bash_scripts/create_instance.sh` | Redirected status message to stderr, added --key-name |
| `terraform_bash_scripts/tf_create.sh` | Added key_name to tfvars |
| `terraform/ec2/main.tf` | Added key_name variable to resource |
| `terraform/ec2/variables.tf` | Added key_name variable definition |

### Files Created
| File | Purpose |
|------|---------|
| `README.md` | Project overview and quick links |
| `docs/QUICK_START.md` | Getting started guide |
| `docs/SSH_SETUP.md` | SSH configuration guide |
| `docs/API_REFERENCE.md` | Complete API documentation |
| `docs/DEPLOYMENT.md` | Deployment stages 1-4 guide |
| `docs/CHANGELOG.md` | This changelog |

### Breaking Changes
- ⚠️ Instance type `t2.micro` is no longer allowed (use `t3.micro` instead)
- ⚠️ Non-whitelisted AMIs are rejected (use whitelisted AMIs from docs)

### Known Limitations
- No rate limiting on API endpoints
- No authentication/authorization
- Single-region support (can be extended)
- SQLite only (no production database)
- No auto-scaling for Kubernetes deployments
- No monitoring/alerting integration

### Future Roadmap
- [ ] Multi-region support
- [ ] Database migration to PostgreSQL
- [ ] API authentication (JWT, OAuth)
- [ ] Rate limiting and quota management
- [ ] Batch operations endpoint
- [ ] Instance tagging API
- [ ] CloudWatch integration
- [ ] Auto-scaling policies
- [ ] VPC/subnet customization
- [ ] Security group templates

### Deprecations
- None in this release

### Security Notes
- SSH key (`my_ec2_keypair.pem`) must be stored securely
- Never commit `.env` file with credentials
- SMTP password should be app-specific, not main Gmail password
- Security groups are created with default restrictions; SSH must be explicitly allowed
- Instance IDs are stored in local SQLite without encryption

### Performance Notes
- Instance creation takes 30-60 seconds (AWS provisioning time)
- Public IP assignment may take up to 2 minutes for some instance types
- Terraform operations are slower than AWS CLI due to state management
- Email notifications are sent asynchronously (non-blocking)

---

## [1.0] — Initial Release

- FastAPI REST API with 6 endpoints
- Dual backend support (AWS CLI and Terraform)
- Free-tier validation
- Email notifications
- SQLite persistence
- Swagger/OpenAPI documentation
- 4-stage deployment architecture
- Jenkins CI/CD pipelines

---

## How to Report Issues

For bug reports or feature requests:
1. Check existing issues in project repository
2. Review [FAQ section in DEPLOYMENT.md](DEPLOYMENT.md#troubleshooting)
3. Check logs: `docker-compose logs api` or `kubectl logs -f deployment/...`
4. Include:
   - Error message or unexpected behavior
   - Steps to reproduce
   - Environment (Stage 1/2/3/4, OS, Python version)
   - Relevant configuration (redacted credentials)

---

**Last Updated:** February 19, 2026
**Maintained by:** Enrique
**Status:** Production-Ready ✅
