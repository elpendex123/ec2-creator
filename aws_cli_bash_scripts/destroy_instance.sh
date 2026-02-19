#!/bin/bash
set -euo pipefail

INSTANCE_ID="${1:?Instance ID is required}"

aws ec2 terminate-instances --instance-ids "$INSTANCE_ID"

echo "Instance $INSTANCE_ID terminated"
