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

import boto3, os
import json
import numpy as np
import pandas as pd

from pyathena import connect


def write_dicts_to_file(path, data):
    with open(path, 'wb') as fp:
        for d in data:
            fp.write(json.dumps(d).encode("utf-8"))
            fp.write("\n".encode('utf-8'))


def get_feature(connection, start):
    weather_data = '''select date_parse(time,'%%Y-%%m-%%d %%H:%%i:%%s') as datetime, temperature,
              dewpoint, pressure, apparenttemperature, windspeed, humidity
              from "meter-data".weather_hourly_london
              where time >= '%s'
              order by 1;
              ''' % start
    df_feature = pd.read_sql(weather_data, connection)
    df_feature = df_feature.set_index('datetime')
    return df_feature


def get_meters(connection, start, end):
    selected_households = '''select meterid, stdortou as cat1, acorn_grouped as cat2
                  from "meter-data".london_acorn_data where meterid between '%s' and '%s' order by meterid;
                  ''' % (start, end)

    df = pd.read_sql(selected_households, connection)
    hh_dict = {}
    # make sure convert numbers to int first, otherwise json serializer cannot recognize int64 type
    for i in df.index:
        hh_dict[df['meterid'][i]] = [int(df['cat1'][i]), int(df['cat2'][i])]
    return hh_dict


def lambda_handler(event, context):
    ATHENA_OUTPUT_BUCKET = event['Athena_bucket']
    S3_BUCKET = event['S3_bucket']
    BATCH_START = event['Batch_start']
    BATCH_END = event['Batch_end']
    DATA_START = event['Data_start']
    DATA_END = event['Data_end']
    FORECAST_PERIOD = event['Forecast_period']
    prediction_length = FORECAST_PERIOD * 24

    region = 'us-east-1'
    connection = connect(s3_staging_dir='s3://{}/'.format(ATHENA_OUTPUT_BUCKET), region_name=region)

    df_feature = get_feature(connection, DATA_START)
    hh_dict = get_meters(connection, BATCH_START, BATCH_END)

    # test data
    todo_query = '''select date_trunc('HOUR', reading_date_time) as datetime, meter_id, sum(reading_value) from "meter-data".daily
              where meter_id in ('%s')
              and datetime >= timestamp '%s'
              and datetime < timestamp '%s'
              group by 2, 1
              ;''' %  ("','".join(hh_dict.keys()), DATA_START, DATA_END)

    batch_job = pd.read_sql(todo_query, connection)
    batch_job = batch_job.set_index('datetime')
    print("read meter data from data lake")

    batchseries = {}
    for meter_id in hh_dict.keys():
        data_kw = batch_job[batch_job['meter_id'] == meter_id].resample('1H').sum()
        batchseries[meter_id] = np.trim_zeros(data_kw.iloc[:,0], trim='f')

    freq = 'H'
    start_dataset = pd.Timestamp(DATA_START, freq=freq)
    end_training = pd.Timestamp(DATA_END, freq=freq) - pd.Timedelta(1, unit='H')
    end_prediction = end_training + pd.Timedelta(prediction_length, unit='H')

    batch_data = [
        {
            "start": str(start_dataset),
            "target": ts[start_dataset:end_training - pd.Timedelta(1, unit='H')].tolist(),  # We use -1, because pandas indexing includes the upper bound
            "cat": hh_dict[meterid],
            "dynamic_feat": [df_feature['temperature'][start_dataset:end_prediction].tolist(),
                             df_feature['humidity'][start_dataset:end_prediction].tolist(),
                             df_feature['apparenttemperature'][start_dataset:end_prediction].tolist()]
        }
        for meterid, ts in batchseries.items()
    ]

    write_dicts_to_file("/tmp/batch.json", batch_data)
    print("generated JSON training data")

    boto3.Session().resource('s3').Bucket(S3_BUCKET).Object(os.path.join('smartmeter', 'input/batch_%s_%s/batch.json' % (BATCH_START, BATCH_END))).upload_file('/tmp/batch.json')

    print('Finished preparing batch data from %s, %s' % (BATCH_START, BATCH_END))