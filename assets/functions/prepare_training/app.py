'''
Input event payload expected to be in the following format:

{
  "Athena_bucket": "aws-athena-query-results-us-east-1-849779837104",
  "S3_bucket": "temp-meter-data-bucket",
  "Data_start": "2013-06-01",
  "Data_end": "2014-01-01",
  "Forecast_period": 7,
  "Training_samples": 50,
  "With_weather_data": 0,
  "Training_instance_type": "ml.c4.2xlarge",
  "Training_job_name": "ml-training-6132fffb71ad463fbb7aaa4f62911227",
  "ML_model_name": "ml-model-6132fffb71ad463fbb7aaa4f62911227",
  "Endpoint_instance_type": "ml.m4.xlarge",
  "ML_endpoint_name": "ml-endpoint-6132fffb71ad463fbb7aaa4f62911227"
}

          do we want to batch data by index
          select meterid, cat1, cat2 from (
            select meterid, stdortou as cat1, acorn_grouped as cat2,
            (row_number() over(order by meterid) ) as row_num
            from ml.acorn_data
          )
          where row_num between 1 and 50;
'''

import sys

import boto3, os, io
import json
import numpy as np
import pandas as pd

from pyathena import connect

def get_weather(connection, start):
    weather_data = '''select date_parse(time,'%Y-%m-%d %H:%i:%s') as datetime, temperature, 
    dewpoint, pressure, apparenttemperature, windspeed, humidity 
    from "meter-data".weather_hourly_london
    where time >= '{}'
    order by 1;
    '''.format(start)
    df_weather = pd.read_sql(weather_data, connection)
    df_weather = df_weather.set_index('datetime')
    return df_weather

def get_meters(connection, samples):
    selected_households = '''select distinct meter_id
        from "meter-data".daily limit {};'''.format(samples)

    df_meters = pd.read_sql(selected_households, connection)
    return df_meters['meter_id'].tolist()

def write_upload_file(bucket, path, data):
    jsonBuffer = io.StringIO()
    for d in data:
        jsonBuffer.write(json.dumps(d))
        jsonBuffer.write('\n')

    boto3.Session().resource('s3').Bucket(bucket).Object(path).put(Body=jsonBuffer.getvalue())

def lambda_handler(event, context):
    ATHENA_OUTPUT_BUCKET = event['Athen_bucket']
    S3_BUCKET = event['S3_bucket']
    TRAINING_SAMPLES = event['Training_samples']
    USE_WEATHER_DATA = event['With_weather_data']
    DATA_START = event['Data_start']
    DATA_END = event['Data_end']
    FORECAST_PERIOD = event['Forecast_period']
    prediction_length = FORECAST_PERIOD * 24

    # region should be an environment variable
    region = 'us-east-1'
    connection = connect(s3_staging_dir='s3://{}/'.format(ATHENA_OUTPUT_BUCKET), region_name=region)

    meter_samples = get_meters(connection, TRAINING_SAMPLES)

    q = '''
            select date_trunc('HOUR', reading_date_time) as datetime, meter_id, sum(reading_value) as consumption
                from "meter-data".daily
                where meter_id in ('{}')
                and reading_date_time >= timestamp '{}'
                and reading_date_time < timestamp '{}'
                group by 2, 1
        '''.format("','".join(meter_samples), DATA_START, DATA_END)

    result = pd.read_sql(q, connection)
    result = result.set_index('datetime')

    timeseries = {}
    for meter_id in meter_samples:
        data_kw = result[result['meter_id'] == meter_id].resample('1H').sum()
        timeseries[meter_id] = data_kw.iloc[:,0]  #np.trim_zeros(data_kw.iloc[:,0], trim='f')

    freq = 'H'
    num_test_windows = 2
    start_dataset = pd.Timestamp(DATA_START, freq=freq)
    end_dataset = pd.Timestamp(DATA_END, freq=freq) - pd.Timedelta(1, unit='H')
    end_training = end_dataset - pd.Timedelta(prediction_length * num_test_windows, unit='H')

    if USE_WEATHER_DATA == 1:
        df_weather = get_weather(connection, DATA_START)

        training_data = [
          {
              "start": str(start_dataset),
              "target": ts[start_dataset:end_training].tolist(),  # We use -1, because pandas indexing includes the upper bound
              "dynamic_feat": [df_weather['temperature'][start_dataset:start_dataset + pd.Timedelta(ts[start_dataset:end_training].size-1, unit='H')].tolist(),
                               df_weather['humidity'][start_dataset:start_dataset + pd.Timedelta(ts[start_dataset:end_training].size-1, unit='H')].tolist(),
                               df_weather['apparenttemperature'][start_dataset:start_dataset + pd.Timedelta(ts[start_dataset:end_training].size-1, unit='H')].tolist()]
          }
          for meterid, ts in timeseries.items()
        ]

        # there could be missing data, so use actual timeseries size
        testing_data = [
            {
                "start": str(start_dataset),
                "target": ts[start_dataset:end_dataset].tolist(),
                "dynamic_feat": [df_weather['temperature'][start_dataset:start_dataset + pd.Timedelta(ts[start_dataset:end_dataset].size-1, unit='H')].tolist(),
                                 df_weather['humidity'][start_dataset:start_dataset + pd.Timedelta(ts[start_dataset:end_dataset].size-1, unit='H')].tolist(),
                                 df_weather['apparenttemperature'][start_dataset:start_dataset + pd.Timedelta(ts[start_dataset:end_dataset].size-1, unit='H')].tolist()]
            }
            for k in range(1, num_test_windows + 1)
            for meterid, ts in timeseries.items()
        ]
    else:
        training_data = [
          {
              "start": str(start_dataset),
              "target": ts[start_dataset:end_training].tolist()  # We use -1, because pandas indexing includes the upper bound
          }
          for meterid, ts in timeseries.items()
        ]

        testing_data = [
            {
                "start": str(start_dataset),
                "target": ts[start_dataset:end_dataset].tolist()
            }
            for k in range(1, num_test_windows + 1)
            for meterid, ts in timeseries.items()
        ]

    write_upload_file(S3_BUCKET, 'smartmeter/sagemaker/train/training.json', training_data)
    write_upload_file(S3_BUCKET, 'smartmeter/sagemaker/test/testing.json', testing_data)
