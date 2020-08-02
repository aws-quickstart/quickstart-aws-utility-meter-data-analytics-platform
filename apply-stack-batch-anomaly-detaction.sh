#!/usr/bin/env bash
aws cloudformation create-stack --stack-name ml-prediction-pipeline \
                                --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND \
                                --template-body file://templates/prediction/template.yaml \
                                --parameters file://stack-parameter-ml-prediction-pipeline.json