#!/bin/bash
set -euo pipefail

NAME="${1:?Name is required}"
AMI="${2:?AMI is required}"
INSTANCE_TYPE="${3:?Instance type is required}"
STORAGE_GB="${4:?Storage GB is required}"

# Create/select workspace
terraform workspace new "$NAME" 2>/dev/null || terraform workspace select "$NAME"

# Write terraform variables file
cat > terraform.tfvars <<EOF
name          = "$NAME"
ami           = "$AMI"
instance_type = "$INSTANCE_TYPE"
storage_gb    = $STORAGE_GB
key_name      = "my_ec2_keypair"
EOF

# Apply terraform
terraform apply -auto-approve -no-color

# Output instance ID and public IP
INSTANCE_ID=$(terraform output -raw instance_id)
PUBLIC_IP=$(terraform output -raw public_ip)

echo "$INSTANCE_ID|$PUBLIC_IP"
