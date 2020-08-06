#!/usr/bin/env bash
aws cloudformation create-stack --stack-name meter-data-lake \
                                --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND CAPABILITY_NAMED_IAM \
                                --template-body file://templates/master.yaml \
                                --parameters file://stack-parameter.json