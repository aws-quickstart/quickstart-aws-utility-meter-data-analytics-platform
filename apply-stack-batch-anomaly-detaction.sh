#!/usr/bin/env bash
aws cloudformation create-stack --stack-name batch-anomaly-detection \
                                --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND \
                                --template-body file://templates/prediction/batch-anomaly-detection.yaml \
                                --parameters file://stack-parameter2.json