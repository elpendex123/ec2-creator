#!/bin/bash
set -euo pipefail

INSTANCE_ID="${1:?Instance ID is required}"

# Use AWS CLI to stop (Terraform doesn't natively start/stop)
aws ec2 stop-instances --instance-ids "$INSTANCE_ID"
aws ec2 wait instance-stopped --instance-ids "$INSTANCE_ID"

echo "Instance $INSTANCE_ID stopped"
