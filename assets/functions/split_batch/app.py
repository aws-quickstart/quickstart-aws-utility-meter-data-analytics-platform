'''
sample lambda input
{
    "Meter_start": 1,
    "Meter_end": 100,
    "Batch_size": 20,
}

'''
import uuid, os

def lambda_handler(event, context):
    start       = event['Meter_start']
    end         = event['Meter_end']
    batchsize   = event['Batch_size']
    s3_bucket   = os.environ['Working_bucket']

    id = uuid.uuid4().hex
    batchdetail = []

    # Cap the batch size to 100 so the lambda function doesn't timeout
    if batchsize > 100:
        batchsize = 100
    for a in range(start, end, batchsize):
        job = {}
        meter_start = 'MAC{}'.format(str(a).zfill(6))
        meter_end = 'MAC{}'.format(str(a+batchsize-1).zfill(6))
        # Sagemaker transform job name cannot be more than 64 characters.
        job['Batch_job'] = 'job-{}-{}-{}'.format(id, meter_start, meter_end)
        job['Batch_start'] = meter_start
        job['Batch_end'] = meter_end
        job['Batch_input'] = 's3://{}/meteranalytics/input/batch_{}_{}'.format(s3_bucket, meter_start, meter_end)
        job['Batch_output'] = 's3://{}/meteranalytics/inference/batch_{}_{}'.format(s3_bucket, meter_start, meter_end)
        batchdetail.append(job)

    # TODO implement
    return batchdetail