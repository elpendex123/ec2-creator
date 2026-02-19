#!/bin/bash
set -euo pipefail

INSTANCE_ID="${1:?Instance ID is required}"

# Use AWS CLI to start (Terraform doesn't natively start/stop)
aws ec2 start-instances --instance-ids "$INSTANCE_ID"
aws ec2 wait instance-running --instance-ids "$INSTANCE_ID"

echo "Instance $INSTANCE_ID started"
