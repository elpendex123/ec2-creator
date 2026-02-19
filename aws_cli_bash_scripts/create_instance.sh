#!/bin/bash
set -euo pipefail

NAME="${1:?Name is required}"
AMI="${2:?AMI is required}"
INSTANCE_TYPE="${3:?Instance type is required}"
STORAGE_GB="${4:?Storage GB is required}"

# Create instance with EBS volume
OUTPUT=$(aws ec2 run-instances \
  --image-id "$AMI" \
  --instance-type "$INSTANCE_TYPE" \
  --key-name my_ec2_keypair \
  --block-device-mappings "DeviceName=/dev/xvda,Ebs={VolumeSize=$STORAGE_GB,VolumeType=gp2}" \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$NAME}]" \
  --query 'Instances[0].[InstanceId,PublicIpAddress]' \
  --output text)

INSTANCE_ID=$(echo "$OUTPUT" | awk '{print $1}')
PUBLIC_IP=$(echo "$OUTPUT" | awk '{print $2}')

# Wait for instance to have a public IP if not assigned yet
if [ -z "$PUBLIC_IP" ] || [ "$PUBLIC_IP" == "None" ]; then
  echo "Waiting for public IP to be assigned..." >&2
  for i in {1..30}; do
    PUBLIC_IP=$(aws ec2 describe-instances \
      --instance-ids "$INSTANCE_ID" \
      --query 'Reservations[0].Instances[0].PublicIpAddress' \
      --output text)

    if [ -n "$PUBLIC_IP" ] && [ "$PUBLIC_IP" != "None" ]; then
      break
    fi
    sleep 2
  done
fi

echo "$INSTANCE_ID|$PUBLIC_IP"
