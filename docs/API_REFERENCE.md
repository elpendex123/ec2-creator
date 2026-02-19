# EC2 Provisioner — API Reference

Complete documentation for all REST API endpoints.

## Base URL

```
http://localhost:8000
```

## Authentication

No authentication required (internal API). All endpoints are publicly accessible.

## Query Parameters (Global)

All endpoints accept an optional `backend` query parameter to select the provisioning backend:

- `?backend=awscli` — Use AWS CLI backend (default)
- `?backend=terraform` — Use Terraform backend

Example:
```bash
curl http://localhost:8000/instances?backend=terraform
```

## Endpoints

### Health Check

**GET** `/health`

Check if the API is running.

**Response:**
```json
{
  "status": "ok"
}
```

**Example:**
```bash
curl http://localhost:8000/health
```

---

### Create Instance

**POST** `/instances`

Provision a new EC2 instance.

**Request Body:**
```json
{
  "name": "string",           # Instance name (required)
  "ami": "string",            # AMI ID (required)
  "instance_type": "string",  # t3.micro or t4g.micro (required)
  "storage_gb": "integer"     # Storage in GB, >= 1 (required)
}
```

**Validation:**
- `instance_type` must be `t3.micro` or `t4g.micro` (free-tier only)
- `ami` must be a whitelisted free-tier AMI for the region
- `storage_gb` must be >= 1

**Response (HTTP 201):**
```json
{
  "id": "i-0cc1d9f4272fd6258",
  "name": "my-server",
  "public_ip": "54.87.149.89",
  "ssh_string": "ssh -i ~/.ssh/your-key.pem ec2-user@54.87.149.89",
  "state": "running",
  "ami": "ami-026992d753d5622bc",
  "instance_type": "t3.micro",
  "backend_used": "awscli",
  "created_at": "2026-02-19T04:44:32.468551"
}
```

**Response (HTTP 400 - Validation Error):**
```json
{
  "detail": "Instance type 't2.micro' or AMI 'ami-xxxxx' not allowed. Only t3.micro and t4g.micro instance types are free tier eligible."
}
```

**Response (HTTP 500 - Creation Error):**
```json
{
  "detail": "Failed to create instance: Script failed: ..."
}
```

**Example:**
```bash
# AWS CLI backend (default)
curl -X POST http://localhost:8000/instances \
  -H "Content-Type: application/json" \
  -d '{
    "name": "web-server",
    "ami": "ami-026992d753d5622bc",
    "instance_type": "t3.micro",
    "storage_gb": 8
  }'

# Terraform backend
curl -X POST "http://localhost:8000/instances?backend=terraform" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "app-server",
    "ami": "ami-026992d753d5622bc",
    "instance_type": "t3.micro",
    "storage_gb": 10
  }'
```

---

### List Instances

**GET** `/instances`

Retrieve all EC2 instances (from local database).

**Response (HTTP 200):**
```json
{
  "instances": [
    {
      "id": "i-0cc1d9f4272fd6258",
      "name": "web-server",
      "public_ip": "54.87.149.89",
      "ssh_string": "ssh -i ~/.ssh/your-key.pem ec2-user@54.87.149.89",
      "state": "running",
      "ami": "ami-026992d753d5622bc",
      "instance_type": "t3.micro",
      "backend_used": "awscli",
      "created_at": "2026-02-19T04:44:32.468551"
    },
    {
      "id": "i-1234567890abcdef0",
      "name": "app-server",
      "public_ip": "54.123.45.67",
      "ssh_string": "ssh -i ~/.ssh/your-key.pem ec2-user@54.123.45.67",
      "state": "stopped",
      "ami": "ami-026992d753d5622bc",
      "instance_type": "t3.micro",
      "backend_used": "terraform",
      "created_at": "2026-02-18T10:00:00.000000"
    }
  ]
}
```

**Example:**
```bash
curl http://localhost:8000/instances
```

---

### Get Instance Details

**GET** `/instances/{instance_id}`

Retrieve details of a specific instance.

**Parameters:**
- `instance_id` (path) — AWS instance ID (e.g., `i-0cc1d9f4272fd6258`)

**Response (HTTP 200):**
```json
{
  "id": "i-0cc1d9f4272fd6258",
  "name": "web-server",
  "public_ip": "54.87.149.89",
  "ssh_string": "ssh -i ~/.ssh/your-key.pem ec2-user@54.87.149.89",
  "state": "running",
  "ami": "ami-026992d753d5622bc",
  "instance_type": "t3.micro",
  "backend_used": "awscli",
  "created_at": "2026-02-19T04:44:32.468551"
}
```

**Response (HTTP 404):**
```json
{
  "detail": "Instance not found: i-0cc1d9f4272fd6258"
}
```

**Example:**
```bash
curl http://localhost:8000/instances/i-0cc1d9f4272fd6258
```

---

### Start Instance

**POST** `/instances/{instance_id}/start`

Start a stopped EC2 instance.

**Parameters:**
- `instance_id` (path) — AWS instance ID

**Response (HTTP 200):**
```json
{
  "id": "i-0cc1d9f4272fd6258",
  "name": "web-server",
  "public_ip": "54.87.149.89",
  "ssh_string": "ssh -i ~/.ssh/your-key.pem ec2-user@54.87.149.89",
  "state": "running",
  "ami": "ami-026992d753d5622bc",
  "instance_type": "t3.micro",
  "backend_used": "awscli",
  "created_at": "2026-02-19T04:44:32.468551"
}
```

**Response (HTTP 404):**
```json
{
  "detail": "Instance not found: i-0cc1d9f4272fd6258"
}
```

**Response (HTTP 500):**
```json
{
  "detail": "Failed to start instance: ..."
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/instances/i-0cc1d9f4272fd6258/start

# With Terraform backend
curl -X POST "http://localhost:8000/instances/i-0cc1d9f4272fd6258/start?backend=terraform"
```

**Email Notification:** ✉️ Sent to `NOTIFICATION_EMAIL` with event type "start"

---

### Stop Instance

**POST** `/instances/{instance_id}/stop`

Stop a running EC2 instance.

**Parameters:**
- `instance_id` (path) — AWS instance ID

**Response (HTTP 200):**
```json
{
  "id": "i-0cc1d9f4272fd6258",
  "name": "web-server",
  "public_ip": "54.87.149.89",
  "ssh_string": "ssh -i ~/.ssh/your-key.pem ec2-user@54.87.149.89",
  "state": "stopped",
  "ami": "ami-026992d753d5622bc",
  "instance_type": "t3.micro",
  "backend_used": "awscli",
  "created_at": "2026-02-19T04:44:32.468551"
}
```

**Response (HTTP 404):**
```json
{
  "detail": "Instance not found: i-0cc1d9f4272fd6258"
}
```

**Response (HTTP 500):**
```json
{
  "detail": "Failed to stop instance: ..."
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/instances/i-0cc1d9f4272fd6258/stop
```

**Email Notification:** ✉️ Sent to `NOTIFICATION_EMAIL` with event type "stop"

---

### Destroy Instance

**DELETE** `/instances/{instance_id}`

Terminate an EC2 instance (irreversible).

**Parameters:**
- `instance_id` (path) — AWS instance ID

**Response (HTTP 204):**
No content (empty response)

**Response (HTTP 404):**
```json
{
  "detail": "Instance not found: i-0cc1d9f4272fd6258"
}
```

**Response (HTTP 500):**
```json
{
  "detail": "Failed to destroy instance: ..."
}
```

**Example:**
```bash
curl -X DELETE http://localhost:8000/instances/i-0cc1d9f4272fd6258
```

**Email Notification:** ✉️ Sent to `NOTIFICATION_EMAIL` with event type "destroy"

---

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | AWS instance ID (e.g., `i-0cc1d9f4272fd6258`) |
| `name` | string | Instance name (user-provided) |
| `public_ip` | string | Public IP address (empty if not assigned) |
| `ssh_string` | string | SSH command template for connection |
| `state` | string | Instance state: `running`, `stopped`, `terminated` |
| `ami` | string | AMI ID used for the instance |
| `instance_type` | string | Instance type (t3.micro, t4g.micro) |
| `backend_used` | string | Backend used: `awscli` or `terraform` |
| `created_at` | datetime | ISO 8601 timestamp of creation |

---

## Error Codes

| Code | Meaning |
|------|---------|
| 200 | OK — Request succeeded |
| 201 | Created — Resource created successfully |
| 204 | No Content — Successful deletion |
| 400 | Bad Request — Invalid input or validation error |
| 404 | Not Found — Instance or resource not found |
| 500 | Internal Server Error — Server-side failure |

---

## Batch Operations

Currently, the API does not support batch operations. To operate on multiple instances, call endpoints sequentially:

```bash
# Create multiple instances
curl -X POST http://localhost:8000/instances -d '{"name":"server1",...}'
curl -X POST http://localhost:8000/instances -d '{"name":"server2",...}'

# Stop multiple instances
curl -X POST http://localhost:8000/instances/i-111111/stop
curl -X POST http://localhost:8000/instances/i-222222/stop
```

---

## Rate Limiting

No rate limiting is currently implemented. Avoid making excessive parallel requests as backend operations (AWS API, Terraform) may throttle.

---

## Database

All instances are stored in a local SQLite database at `./data/instances.db`. The database persists across API restarts.

To reset the database:
```bash
rm -f ./data/instances.db
# Restart the API
```

---

## Swagger UI

Interactive API documentation is available at:
```
http://localhost:8000/docs
```

Use this to test endpoints directly from your browser.
