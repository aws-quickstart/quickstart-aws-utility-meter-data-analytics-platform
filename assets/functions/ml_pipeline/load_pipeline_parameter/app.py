""" Loads the pipeline parameters from the initial_pass file and passes them back.
    Parameter that gets passed to this function will overwrite the parameter stored in the inital_pass file """

import boto3
import os
import uuid

S3 = boto3.client('s3')
DYNAMODB = boto3.resource('dynamodb')

CONFIG_TABLE_NAME = os.environ['config_table']
STRING = 'S'
NUMBER = 'N'


def get_config(name):
    response = DYNAMODB.Table(CONFIG_TABLE_NAME).get_item(
        Key={'name': name}
    )

    return response['Item']["value"]


def write_config(name, value):
    DYNAMODB.Table(CONFIG_TABLE_NAME).put_item(
        Item={"name": name, "value": value}
    )


def lambda_handler(event, context):

    if 'train_model' in event:
        train_model = event['train_model']
    else:
        train_model = False

    if train_model:
        unique_id = str(uuid.uuid4())

        model_name = "model-{}".format(unique_id)
        job_name = "training-job-{}".format(unique_id)
        endpoint_name = "inference-endpoint-{}".format(unique_id)

        write_config("ModelName", model_name)
        write_config("Training_job_name", job_name)
        write_config("ML_endpoint_name", endpoint_name)

        # TODO reuse endpoint, with new endpoint config

    else:
        model_name = get_config("ModelName")
        job_name = get_config("Training_job_name")
        endpoint_name = get_config("ML_endpoint_name")

    parameter = {
        "Data_start": get_config("Data_start"),
        "Data_end": get_config("Data_end"),
        "Forecast_period": int(get_config("Forecast_period")),
        "Training_samples": int(get_config("Training_samples")),
        "Training_instance_type": get_config("Training_instance_type"),
        "Endpoint_instance_type": get_config("Endpoint_instance_type"),
        "Meter_start": int(get_config("Meter_start")),
        "Meter_end": int(get_config("Meter_end")),
        "Batch_size": int(get_config("Batch_size")),
        "ML_endpoint_name": endpoint_name,
        "ModelName": model_name,
        "Training_job_name": job_name
    }

    return {
        **parameter,
        **event
    }
