#!/bin/bash
set -euo pipefail

aws ec2 describe-instances \
  --query 'Reservations[*].Instances[*].[InstanceId,State.Name,PublicIpAddress,InstanceType,ImageId,LaunchTime]' \
  --output json
