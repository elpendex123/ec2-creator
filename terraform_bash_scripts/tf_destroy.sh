#!/bin/bash
set -euo pipefail

INSTANCE_ID="${1:?Instance ID or workspace name is required}"

# Get the current workspace (assume instance ID maps to workspace name)
# Try to get instance first, then destroy
terraform destroy -auto-approve -no-color

echo "Instance destroyed"
