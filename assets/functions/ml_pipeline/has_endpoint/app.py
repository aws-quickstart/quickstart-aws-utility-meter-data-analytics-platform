import boto3

sagemaker = boto3.client('sagemaker')


def lambda_handler(event, context):
    endpoint_name = event['endpoint_name']

    endpoints = sagemaker.list_endpoints(NameContains=endpoint_name)

    return {
        "has_endpoint": len(endpoints['Endpoints']) > 0
    }