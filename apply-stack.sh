#!/usr/bin/env bash
aws cloudformation create-stack --stack-name meter-data-lake \
                                --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND CAPABILITY_NAMED_IAM \
                                --template-body file://templates/workload.yaml \
                                --parameters file://stack-parameter.json