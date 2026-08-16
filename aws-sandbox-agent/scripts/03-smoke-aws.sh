#!/usr/bin/env bash
# Local AWS smoke: identity + Cost Explorer + EC2 in us-east-2.
# Uses the caller environment (profile/keys). Does not print secrets.
set -euo pipefail

REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-us-east-2}}"
if [[ "$REGION" != "us-east-2" ]]; then
  echo "this smoke test is scoped to us-east-2 (got ${REGION})" >&2
  exit 1
fi

echo "== sts get-caller-identity =="
aws sts get-caller-identity --query '{Account:Account,Arn:Arn}' --output json

START="$(date -u +%Y-%m-01)"
END="$(date -u -d tomorrow +%Y-%m-%d 2>/dev/null || date -u -v+1d +%Y-%m-%d)"

echo
echo "== ce get-cost-and-usage (us-east-2 filter, ${START}..${END}) =="
aws ce get-cost-and-usage \
  --region us-east-1 \
  --time-period "Start=${START},End=${END}" \
  --granularity MONTHLY \
  --metrics UnblendedCost \
  --filter "{\"Dimensions\":{\"Key\":\"REGION\",\"Values\":[\"us-east-2\"]}}" \
  --query 'ResultsByTime[0].Total' \
  --output json

echo
echo "== ec2 describe-instances (us-east-2, running count) =="
aws ec2 describe-instances \
  --region us-east-2 \
  --query 'Reservations[].Instances[].{Id:InstanceId,Type:InstanceType,AZ:Placement.AvailabilityZone,State:State.Name}' \
  --output table

echo
echo "smoke ok (numbers above are ground truth for the kagent chat)"
