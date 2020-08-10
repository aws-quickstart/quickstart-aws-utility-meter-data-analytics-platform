import boto3, os
import uuid

from botocore.errorfactory import ClientError


def check_if_file_exist(bucket, key):
    s3_client = boto3.client('s3')
    file_exists = True
    try:
        s3_client.head_object(Bucket=bucket, Key=key)
    except ClientError:
        file_exists = False
        pass

    return file_exists


def lambda_handler(event, context):
    working_bucket = os.environ['Working_bucket']

    initial_pipeline_passed = check_if_file_exist(working_bucket, "meteranalytics/initial_pass")

    return {
        **event,
        "initial_pipeline_passed": initial_pipeline_passed,
        "Data_start": "2013-06-01",
        "Data_end": "2014-01-01",
        "Forecast_period": 7,
        "Training_samples": 50,
        "With_weather_data": 0,
        "Training_instance_type": "ml.c4.2xlarge",
        "Endpoint_instance_type": "ml.m4.xlarge",
        "Training_job_name": "training_job_{}".format(str(uuid.uuid4())),
        "ModelName": "ml_model_{}".format(str(uuid.uuid4())),
        "ML_endpoint_name": "ml_endpoint_{}".format(str(uuid.uuid4())),
        "Meter_start": 1,
        "Meter_end": 100,
        "Batch_size": 75
    }
