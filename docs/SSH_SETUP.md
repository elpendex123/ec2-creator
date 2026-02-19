# SSH Setup & Key Pair Configuration

Configure SSH access to EC2 instances created by the provisioner.

## Key Pair Name

All instances are created with the key pair: **`my_ec2_keypair`**

This is configured in:
- `aws_cli_bash_scripts/create_instance.sh` (line 14: `--key-name my_ec2_keypair`)
- `terraform/ec2/main.tf` (variable: `key_name = var.key_name`)
- `terraform_bash_scripts/tf_create.sh` (tfvars: `key_name = "my_ec2_keypair"`)

## Prerequisites

### 1. Create an EC2 Key Pair in AWS

If you don't have `my_ec2_keypair` created in AWS, create it first:

```bash
# Create the key pair
aws ec2 create-key-pair --key-name my_ec2_keypair --query 'KeyMaterial' --output text > ~/.ssh/my_ec2_keypair.pem

# Set correct permissions (required for SSH)
chmod 600 ~/.ssh/my_ec2_keypair.pem

# Verify it's readable only by you
ls -la ~/.ssh/my_ec2_keypair.pem
# Should show: -rw------- (600 permissions)
```

### 2. Verify Your Local Key

```bash
ls -la ~/.ssh/my_ec2_keypair.pem
```

You should have:
```
-r-------- 1 enrique enrique  387 Jan 27 22:26 my_ec2_keypair.pem
```

If permissions are wrong, fix them:
```bash
chmod 600 ~/.ssh/my_ec2_keypair.pem
```

## SSH Connection

### Basic SSH Command

```bash
ssh -i ~/.ssh/my_ec2_keypair.pem ec2-user@<PUBLIC_IP>
```

Replace `<PUBLIC_IP>` with the instance's public IP address returned by the API.

### From API Response

When you create an instance, the API returns an `ssh_string`:

```json
{
  "id": "i-0cc1d9f4272fd6258",
  "name": "my-server",
  "public_ip": "54.87.149.89",
  "ssh_string": "ssh -i ~/.ssh/your-key.pem ec2-user@54.87.149.89",
  ...
}
```

**Note:** The `ssh_string` in the response shows `~/.ssh/your-key.pem` as a template. Replace with your actual key path.

### Updated SSH String

Use this format:
```bash
ssh -i ~/.ssh/my_ec2_keypair.pem ec2-user@54.87.149.89
```

## Security Group Configuration

Instances created by the provisioner need SSH access enabled. The provisioner does NOT automatically configure security groups for SSH.

### Allow SSH (Port 22) on Security Group

**First time setup (if security group blocks SSH):**

```bash
# Find the security group ID
aws ec2 describe-instances --instance-ids i-0cc1d9f4272fd6258 \
  --query 'Reservations[0].Instances[0].SecurityGroups[0].GroupId' \
  --output text

# Allow SSH from anywhere (⚠️ not recommended for production)
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxxxxx \
  --protocol tcp \
  --port 22 \
  --cidr 0.0.0.0/0
```

**For production:** Restrict SSH to your IP or corporate network:
```bash
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxxxxx \
  --protocol tcp \
  --port 22 \
  --cidr YOUR_IP/32
```

## Troubleshooting

### "Permission denied (publickey)"

**Problem:** SSH key permissions are wrong or key doesn't match.

**Solutions:**
```bash
# Check key permissions
ls -la ~/.ssh/my_ec2_keypair.pem
# Must be 600 (rw-------)

# Fix if needed
chmod 600 ~/.ssh/my_ec2_keypair.pem

# Verify the key is in AWS
aws ec2 describe-key-pairs --key-names my_ec2_keypair
```

### "Connection timed out"

**Problem:** Security group doesn't allow SSH or instance is not ready.

**Solutions:**
```bash
# Check instance state
aws ec2 describe-instances --instance-ids i-xxxxx \
  --query 'Reservations[0].Instances[0].State.Name' --output text
# Should show: "running"

# Check security group allows port 22
aws ec2 describe-security-groups --group-ids sg-xxxxx \
  --query 'SecurityGroups[0].IpPermissions' --output table

# Authorize SSH if needed (see "Allow SSH" section above)
```

### "Host key verification failed"

**Problem:** SSH host key not in known_hosts yet.

**Solution:** Accept the host key on first connection:
```bash
ssh -i ~/.ssh/my_ec2_keypair.pem ec2-user@54.87.149.89
# Type 'yes' when prompted "Are you sure you want to continue connecting?"
```

### Can't find key file

**Problem:** Key file path is wrong.

**Solutions:**
```bash
# List available keys
ls -la ~/.ssh/

# Make sure my_ec2_keypair.pem exists
# Use absolute path in SSH command
ssh -i /home/enrique/.ssh/my_ec2_keypair.pem ec2-user@54.87.149.89
```

## Advanced: SSH Config

Create `~/.ssh/config` for easier connections:

```
Host ec2-provisioner
    HostName %h
    User ec2-user
    IdentityFile ~/.ssh/my_ec2_keypair.pem
    StrictHostKeyChecking accept-new
```

Then connect with:
```bash
ssh -i ~/.ssh/my_ec2_keypair.pem ec2-user@<IP>
# Or use the config:
# ssh ec2-provisioner <IP>
```

## Updating Key Pair Configuration

To use a **different key pair** instead of `my_ec2_keypair`:

### 1. Update Shell Script

Edit `aws_cli_bash_scripts/create_instance.sh`:
```bash
--key-name your_new_keypair \
```

### 2. Update Terraform Script

Edit `terraform_bash_scripts/tf_create.sh`:
```bash
key_name = "your_new_keypair"
```

### 3. Update Terraform Config

Edit `terraform/ec2/variables.tf`:
```hcl
variable "key_name" {
  default = "your_new_keypair"
}
```

### 4. Ensure Key Exists in AWS

```bash
aws ec2 describe-key-pairs --key-names your_new_keypair
```

If not found, create it:
```bash
aws ec2 create-key-pair --key-name your_new_keypair --query 'KeyMaterial' --output text > ~/.ssh/your_new_keypair.pem
chmod 600 ~/.ssh/your_new_keypair.pem
```
