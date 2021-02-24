'''
sample lambda input
{
    "Meter_start": 1,
    "Meter_end": 100,
    "Batch_size": 20
}
'''

import os
import uuid

import pandas as pd
from pyathena import connect

REGION = os.environ['AWS_REGION']
ATHENA_BUCKET = os.environ['Athena_bucket']
S3_BUCKET = os.environ['Working_bucket']
SCHEMA = os.environ['Db_schema']

ATHENA_CONNECTION = connect(s3_staging_dir='s3://{}/'.format(ATHENA_BUCKET), region_name=REGION)


def lambda_handler(event, context):
    # list index starts from 0
    start = event['Meter_start'] - 1
    end = event['Meter_end'] - 1
    batch_size = event['Batch_size']

    # Todo, more efficient way is to create a meter list table instead of getting it from raw data
    df_meters = pd.read_sql('''select distinct meter_id from "{}".daily order by meter_id'''.format(SCHEMA),
                            ATHENA_CONNECTION)
    meters = df_meters['meter_id'].tolist()

    id = uuid.uuid4().hex
    batchdetail = []

    # Cap the batch size to 100 so the lambda function doesn't timeout
    if batch_size > 100:
        batch_size = 100
    for a in range(start, min(end, len(meters)), batch_size):
        job = {}
        meter_start = meters[a]

        upper_limit = min(end - 1, a + batch_size - 1)
        if upper_limit > len(meters):
            upper_limit = len(meters) - 1

        meter_end = meters[upper_limit]

        # Sagemaker transform job name cannot be more than 64 characters.
        job['Batch_job'] = 'job-{}-{}-{}'.format(id, meter_start, meter_end)
        job['Batch_start'] = meter_start
        job['Batch_end'] = meter_end
        job['Batch_input'] = 's3://{}/meteranalytics/input/batch_{}_{}'.format(S3_BUCKET, meter_start, meter_end)
        job['Batch_output'] = 's3://{}/meteranalytics/inference/batch_{}_{}'.format(S3_BUCKET, meter_start, meter_end)
        batchdetail.append(job)

    return batchdetail
