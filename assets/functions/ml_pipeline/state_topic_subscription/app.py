import os
import boto3

client = boto3.client('stepfunctions')


def trigger_state_machine():
    state_machine_arn = os.environ['ml_pipeline_trigger_state_machine']

    running_executions = client.list_executions(
        stateMachineArn=state_machine_arn,
        statusFilter='RUNNING',
        maxResults=10
    )

    if not running_executions['executions']:
        print('start new execution')
        boto3 \
            .client('stepfunctions') \
            .start_execution(stateMachineArn=state_machine_arn)
    else:
        print('state machine already running.')


def lambda_handler(event, context):
    trigger_state_machine()
