#!/usr/bin/env bash

set -e

BUCKETS=`aws s3 ls`



for bucket in $BUCKETS
do

  if  [[ $bucket == meter-data-* ]] || [[ $bucket == aws-glue-* ]] ;
  then
      echo "Deleting bucket: $bucket"
      {
        sh delete-buckets.sh $bucket
      } || {
        echo "Error deleting bucket: $bucket"
      }
  fi

done

echo "Deleting stack meter-data-lake"
aws cloudformation delete-stack --stack-name meter-data-lake --region us-east-1

aws cloudformation wait stack-delete-complete --stack-name meter-data-lake