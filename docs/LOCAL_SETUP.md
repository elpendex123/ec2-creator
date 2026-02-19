# EC2 Provisioner API — Local Development Setup

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add AWS credentials (optional for local testing)
# For local testing without AWS, you can leave them empty
```

### 3. Start the API Server

```bash
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see output like:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [XXXX] using WatchFiles
INFO:app.main:Initializing database...
INFO:app.main:Database initialized
INFO:     Application startup complete.
```

### 4. Test the API

Open your browser and navigate to:
- **Health Check**: http://localhost:8000/health
- **Interactive API Docs (Swagger UI)**: http://localhost:8000/docs
- **Alternative API Docs (ReDoc)**: http://localhost:8000/redoc

Or run the test script:
```bash
python3 test_api.py
```

---

## API Endpoints

All endpoints are available at `http://localhost:8000`

### Health Check
```bash
GET /health
```
Returns: `{"status": "ok"}`

### List All Instances
```bash
GET /instances
```
Returns: `{"instances": [...]}`

### Get Single Instance
```bash
GET /instances/{instance_id}
```

### Create Instance
```bash
POST /instances
Content-Type: application/json

{
  "name": "my-server",
  "ami": "ami-0c02fb55956c7d316",
  "instance_type": "t2.micro",
  "storage_gb": 8
}
```

**Query Parameters:**
- `?backend=terraform` — Use Terraform (default)
- `?backend=awscli` — Use AWS CLI

**Example:**
```bash
POST /instances?backend=awscli
```

### Start Instance
```bash
POST /instances/{instance_id}/start
```

### Stop Instance
```bash
POST /instances/{instance_id}/stop
```

### Destroy Instance
```bash
DELETE /instances/{instance_id}
```

---

## Using Swagger UI

The interactive API documentation is available at: **http://localhost:8000/docs**

From there you can:
- View all endpoints
- Try out API calls directly in the browser
- See request/response examples
- View validation rules

---

## Database

The SQLite database is stored at: `./data/instances.db`

It's automatically created on first run with the following schema:
```sql
id            TEXT PRIMARY KEY   -- AWS instance ID
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

---

## Free Tier Validation

The API enforces free tier eligibility:

**Allowed Instance Types:**
- `t2.micro`
- `t3.micro`

**Allowed AMIs** (per region):
- **us-east-1**: `ami-0c02fb55956c7d316`, `ami-026ebee89baf5eb77`
- **us-east-2**: `ami-0ea3c35d6814e3cb6`, `ami-0229d9f8ca82508cc`
- **us-west-1**: `ami-0fb653ca2d3203ac1`, `ami-0f4c5fd4dd4dd1051`
- **us-west-2**: `ami-0430580de6244e02b`, `ami-0e472933a1666f130`
- **eu-west-1**: `ami-0d3d0c0e87e3a77fd`, `ami-0f1a8f29ed2ad83e2`

Invalid requests return HTTP 400 with a descriptive error.

---

## Environment Variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `AWS_ACCESS_KEY_ID` | No | - | AWS credentials |
| `AWS_SECRET_ACCESS_KEY` | No | - | AWS credentials |
| `AWS_DEFAULT_REGION` | No | `us-east-1` | AWS region |
| `BACKEND` | No | `terraform` | Default backend (terraform or awscli) |
| `DB_PATH` | No | `./data/instances.db` | SQLite database path |
| `SMTP_HOST` | No | `smtp.gmail.com` | Email notifications |
| `SMTP_PORT` | No | `587` | SMTP port |
| `SMTP_USER` | No | - | Email account |
| `SMTP_PASSWORD` | No | - | Email password |
| `NOTIFICATION_EMAIL` | No | - | Recipient for notifications |

---

## Testing with cURL

### Health Check
```bash
curl http://localhost:8000/health
```

### List Instances
```bash
curl http://localhost:8000/instances
```

### Invalid Instance Type (should return 400)
```bash
curl -X POST http://localhost:8000/instances \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test",
    "ami": "ami-0c02fb55956c7d316",
    "instance_type": "t2.large",
    "storage_gb": 8
  }'
```

### View Full Test Output
```bash
python3 test_api.py
```

---

## Troubleshooting

### Port Already in Use
If port 8000 is already in use:
```bash
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### ModuleNotFoundError
Make sure you've installed dependencies:
```bash
pip install -r requirements.txt
```

### Database Locked
If you see "database is locked" errors:
1. Stop the API server
2. Delete `data/instances.db`
3. Restart the server (it will recreate the DB)

### Permission Denied on Bash Scripts
If AWS CLI or Terraform operations fail with permission errors:
```bash
chmod +x aws_cli_bash_scripts/*.sh
chmod +x terraform_bash_scripts/*.sh
```

---

## Next Steps

Once local development is working, you can:

1. **Add AWS credentials** to `.env` to test actual EC2 operations
2. **Run linting**: `flake8 app/`
3. **Run tests**: `pytest` (create tests/ directory with test files)
4. **Build Docker image**: `docker build -t ec2-provisioner:latest .`
5. **Deploy to Docker Compose**: `docker-compose up`
6. **Deploy to Minikube**: `kubectl apply -f k8s/`

---

## Project Structure

```
ec2-creator/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Settings and env vars
│   ├── models/
│   │   └── instance.py      # Pydantic models
│   ├── services/
│   │   ├── db.py            # SQLite operations
│   │   ├── notifications.py # Email sender
│   │   ├── aws_cli.py       # AWS CLI wrapper
│   │   └── terraform.py     # Terraform wrapper
│   └── routers/
│       └── instances.py     # REST endpoints
├── aws_cli_bash_scripts/    # AWS CLI bash scripts
├── terraform_bash_scripts/  # Terraform bash scripts
├── terraform/               # Terraform configurations
├── k8s/                     # Kubernetes manifests
├── jenkins/                 # Jenkins pipelines
├── test_api.py              # API test script
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (local)
└── Dockerfile               # Container build
```

---

## Development Tips

### Auto-Reload
The API runs with `--reload` enabled, so any changes to Python files will automatically restart the server.

### View Database Contents
```bash
sqlite3 ./data/instances.db "SELECT * FROM instances;"
```

### Check API Logs
Logs are printed to stdout. Look for:
- `INFO:` — Standard operations
- `WARNING:` — Potential issues
- `ERROR:` — Failures

### Create a Virtual Environment (Optional)
For better isolation:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

That's it! You now have a fully functional EC2 Provisioner API running locally.
