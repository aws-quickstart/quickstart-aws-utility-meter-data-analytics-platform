'''
Input event payload expected to be in the following format:

{
"Batch_start": "MAC000001",
"Batch_end": "MAC000010",
"Data_start": "2013-06-01",
"Data_end": "2014-01-01",
"Forecast_period": 7
}

'''

import boto3, os
import json
import pandas as pd
import numpy as np

from pyathena import connect

REGION = os.environ['AWS_REGION']
ATHENA_OUTPUT_BUCKET = os.environ['Athena_bucket']
S3_BUCKET = os.environ['Working_bucket']
DB_SCHEMA = os.environ['Db_schema']

ATHENA_CONNECTION = connect(s3_staging_dir='s3://{}/'.format(ATHENA_OUTPUT_BUCKET), region_name=REGION)
S3 = boto3.resource('s3')


def get_meters(connection, start, end, db_schema):
    selected_households = '''select distinct meter_id
                  from "{}".daily where meter_id between '{}' and '{}' order by meter_id;
                  '''.format(db_schema, start, end)

    df_meters = pd.read_sql(selected_households, connection)
    return df_meters['meter_id'].tolist()


def lambda_handler(event, context):
    batch_start = event['Batch_start']
    batch_end = event['Batch_end']
    forecast_start = event['Data_end']
    forecast_period = event['Forecast_period']
    prediction_length = forecast_period * 24

    output = 'meteranalytics/inference/batch_%s_%s/batch.json.out' % (batch_start, batch_end)
    S3.Bucket(S3_BUCKET).Object(output).download_file('/tmp/batch.out.json')

    freq = 'H'
    prediction_time = pd.Timestamp(forecast_start, freq=freq)
    prediction_index = pd.date_range(start=prediction_time,
                                     end=prediction_time + pd.Timedelta(prediction_length - 1, unit='H'), freq=freq)
    dict_of_samples = {}

    meterids = get_meters(ATHENA_CONNECTION, batch_start, batch_end, DB_SCHEMA)

    results = pd.DataFrame(columns=['meterid', 'datetime', 'kwh'])
    i = 0
    with open('/tmp/batch.out.json') as fp:
        for line in fp:
            df = pd.DataFrame(data={**json.loads(line)['quantiles'],
                                    **dict_of_samples}, index=prediction_index)
            dataframe = pd.DataFrame({'meter_id': np.array([meterids[i] for x in range(df['0.9'].count())]),
                                      'datetime': df.index.values,
                                      'consumption': df['0.9'].values})
            i = i + 1
            results = results.append(dataframe)

    results.to_csv('/tmp/forecast.csv', index=False)
    S3.Bucket(S3_BUCKET).Object(os.path.join('meteranalytics',
                                             'forecast/{}/batch_{}_{}.csv'.format(
                                                 forecast_start, batch_start,
                                                 batch_end))).upload_file(
        '/tmp/forecast.csv')
