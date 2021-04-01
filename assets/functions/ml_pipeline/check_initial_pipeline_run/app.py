import boto3
import os
from botocore.errorfactory import ClientError

S3 = boto3.client('s3')


def check_if_file_exist(bucket, key):
    file_exists = True
    try:
        S3.head_object(Bucket=bucket, Key=key)
    except ClientError:
        file_exists = False
        pass

    return file_exists


def lambda_handler(event, context):
    working_bucket = os.environ['Working_bucket']
    file_key = "meteranalytics/initial_pass"

    initial_pipeline_passed = check_if_file_exist(working_bucket, file_key)

    return {
        "initial_pipeline_passed": initial_pipeline_passed
    }
