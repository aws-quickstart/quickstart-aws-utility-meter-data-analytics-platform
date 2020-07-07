'''
          Input event payload expected to be in the following format:

          {
            "Batch_start": "MAC000001",
            "Batch_end": "MAC000010",
            "Data_start": "2013-06-01",
            "Data_end": "2014-01-01",
            "Forecast_period": 7
          }

          do we want to batch data by index
          select meterid, cat1, cat2 from (
            select meterid, stdortou as cat1, acorn_grouped as cat2,
            (row_number() over(order by meterid) ) as row_num
            from ml.acorn_data
          )
          where row_num between 1 and 50;
          '''

import boto3, io
import pandas as pd

from pyathena import connect


def lambda_handler(event, context):
    ATHENA_OUTPUT_BUCKET = event['Athena_bucket']
    S3_BUCKET = event['S3_bucket']
    BATCH_START = event['Batch_start']
    BATCH_END = event['Batch_end']
    start_datetime = event['Data_start']
    end_datetime = event['Data_end']
    FORECAST_PERIOD = event['Forecast_period']
    prediction_length = FORECAST_PERIOD * 24

    region = 'us-east-1'
    connection = connect(s3_staging_dir='s3://{}/'.format(ATHENA_OUTPUT_BUCKET), region_name=region)

    q = '''
            select date_trunc('HOUR', reading_date_time) as datetime, meter_id, sum(reading_value) as consumption
                from "meter-data".daily
                where reading_date_time >= timestamp '{}'
                and reading_date_time < timestamp '{}'
                group by 2, 1
        '''.format(start_datetime, end_datetime)

    result = pd.read_sql(q, connection)

    # pd.set_option('display.max_rows', 20)
    # train_data, validation_data, test_data = np.split(result.sample(frac=1, random_state=1729), [int(0.7 * len(result)), int(0.9 * len(result))])

    path = "smartmeter/input/batch_{}_{}/batch.json".format(start_datetime, end_datetime)
    jsonBuffer = io.StringIO()
    result.to_json(jsonBuffer, orient='records')

    boto3.Session().resource('s3').Bucket(S3_BUCKET).Object(path).put(Body=jsonBuffer.getvalue())
