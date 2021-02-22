""" Loads the pipeline parameters from the initial_pass file and passes them back.
    Parameter that gets passed to this function will overwrite the parameter stored in the inital_pass file """

import boto3
import os

S3 = boto3.client('s3')
DYNAMODB = boto3.client('dynamodb')

CONFIG_TABLE_NAME = os.environ['config_table']
STRING = 'S'
NUMBER = 'N'


def get_config(name, expected_type=STRING):
    response = DYNAMODB.get_item(
        TableName=CONFIG_TABLE_NAME,
        Key={
            'name': {'S': name}
        }
    )

    if(expected_type == NUMBER):
        return int(response['Item']["value"][expected_type])
    else:
        return response['Item']["value"][expected_type]


def lambda_handler(event, context):
    parameter = {
        "Data_start": get_config("Data_start"),
        "Data_end": get_config("Data_end"),
        "Forecast_period": get_config("Forecast_period", NUMBER),
        "Training_samples": get_config("Training_samples", NUMBER),
        "Training_instance_type": get_config("Training_instance_type"),
        "Endpoint_instance_type": get_config("Endpoint_instance_type"),
        "Training_job_name": get_config("Training_job_name"),
        "ModelName": get_config("ModelName"),
        "ML_endpoint_name": get_config("ML_endpoint_name"),
        "Meter_start": get_config("Meter_start", NUMBER),
        "Meter_end": get_config("Meter_end", NUMBER),
        "Batch_size": get_config("Batch_size", NUMBER)
    }

    return {
        **parameter,
        **event
    }
