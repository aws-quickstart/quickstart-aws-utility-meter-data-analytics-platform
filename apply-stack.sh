#!/usr/bin/env bash

set -e

REGION=${1:-us-east-1}

echo "Checking if stack exists ..."

if ! aws cloudformation describe-stacks --region $REGION --stack-name meter-data-lake ; then

  echo -e "\nStack does not exist, creating ..."
  aws cloudformation create-stack --stack-name meter-data-lake \
                                --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND CAPABILITY_NAMED_IAM \
                                --template-body file://templates/main.template.yaml \
                                --parameters file://stack-parameter-vpc.json \
                                --region $REGION

  echo "Waiting for stack to be created ..."
  aws cloudformation wait stack-create-complete --stack-name meter-data-lake --region $REGION

else

  echo -e "\nStack exists, attempting update ..."

  set +e
  update_output=$(
  aws cloudformation update-stack --stack-name meter-data-lake \
                                --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND CAPABILITY_NAMED_IAM \
                                --template-body file://templates/main.template.yaml \
                                --parameters file://stack-parameter-vpc.json \
                                --region $REGION \
                                2>&1)
  status=$?
  set -e

  echo "$update_output"

  if [ $status -ne 0 ] ; then

    # Don't fail for no-op update
    if [[ $update_output == *"ValidationError"* && $update_output == *"No updates"* ]] ; then
      echo -e "\nFinished create/update - no updates to be performed"
      exit 0
    else
      exit $status
    fi

  fi

  echo "Waiting for stack update to complete ..."
  aws cloudformation wait stack-update-complete --stack-name meter-data-lake --region $REGION

fi

echo "Finished create/update successfully!"