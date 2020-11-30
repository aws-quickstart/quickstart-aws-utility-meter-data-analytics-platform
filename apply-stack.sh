#!/usr/bin/env bash

set -e

REGION="us-east-1"

aws cloudformation create-stack --stack-name meter-data-lake \
                                --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND CAPABILITY_NAMED_IAM \
                                --template-body file://templates/workload.template.yaml \
                                --parameters file://stack-parameter.json \
                                --region $REGION

aws cloudformation wait stack-create-complete --stack-name meter-data-lake --region $REGION