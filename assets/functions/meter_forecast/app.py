'''
Testing event
{
  "Data_start": "2013-06-01",
  "Data_end": "2014-01-01",
  "Forecast_period": 7,
  "Meter_id": "MAC004534",
  "With_weather_data": 1,
  "ML_endpoint_name": "ml-endpoint-0001"
}
'''

import boto3, os
import pandas as pd 
import numpy as np
import json
from pyathena import connect 
    
def get_weather(connection, start, db_schema):
    weather_data = '''select date_parse(time,'%Y-%m-%d %H:%i:%s') as datetime, temperature,
    apparenttemperature, humidity
    from "{}".weather
    where time >= '{}'
    order by 1;
    '''.format(db_schema, start)
    df_weather = pd.read_sql(weather_data, connection)
    df_weather = df_weather.set_index('datetime')
    return df_weather
    
def encode_request(ts, weather):
    instance = {
          "start": str(ts.index[0]),
          "target": [x if np.isfinite(x) else "NaN" for x in ts]    
        }
    if weather is not None:
        instance["dynamic_feat"] = [weather['temperature'].tolist(),
                                  weather['humidity'].tolist(),
                                  weather['apparenttemperature'].tolist()]

    configuration = {
        "num_samples": 100,
        "output_types": ["quantiles"] ,
        "quantiles": ["0.9"]
    }

    http_request_data = {
        "instances": [instance],
        "configuration": configuration
    }

    return json.dumps(http_request_data).encode('utf-8')

def decode_response(response, freq, prediction_time):
    predictions = json.loads(response.decode('utf-8'))['predictions'][0]
    prediction_length = len(next(iter(predictions['quantiles'].values())))
    prediction_index = pd.date_range(start=prediction_time, end=prediction_time + pd.Timedelta(prediction_length-1, unit='H'), freq=freq)
    dict_of_samples = {}
    return pd.DataFrame(data={**predictions['quantiles'], **dict_of_samples}, index=prediction_index)


def lambda_handler(event, context):
    ATHENA_OUTPUT_BUCKET = os.environ['Athena_bucket']
    DB_SCHEMA = os.environ['Db_schema']

    parameter = event
    if "body" in event:
        parameter = json.loads(event["body"])

    METER_ID = parameter['Meter_id']
    ML_ENDPOINT_NAME = parameter['ML_endpoint_name']
    USE_WEATHER_DATA = parameter['With_weather_data']
    DATA_START = parameter['Data_start']
    DATA_END = parameter['Data_end']

    region = 'us-east-1'
    connection = connect(s3_staging_dir='s3://{}/'.format(ATHENA_OUTPUT_BUCKET), region_name=region)
    query = '''select date_trunc('HOUR', reading_date_time) as datetime, sum(reading_value) as consumption
                from "{}".daily
                where meter_id = '{}' and reading_date_time >= timestamp '{}'
                and  reading_date_time < timestamp '{}'
                group by 1;
                '''.format(DB_SCHEMA, METER_ID, DATA_START, DATA_END)
    result = pd.read_sql(query, connection)
    result = result.set_index('datetime')

    data_kw = result.resample('1H').sum()
    timeseries = data_kw.iloc[:,0]  #np.trim_zeros(data_kw.iloc[:,0], trim='f')
    
    freq = 'H'
    df_weather = None
    if USE_WEATHER_DATA == 1:
        df_weather = get_weather(connection, DATA_START, DB_SCHEMA)

    runtime= boto3.client('runtime.sagemaker')
    response = runtime.invoke_endpoint(EndpointName=ML_ENDPOINT_NAME,
                                       ContentType='application/json',
                                       Body=encode_request(timeseries[:], df_weather))
    prediction_time = timeseries.index[-1] + pd.Timedelta(1, unit='H')
    df_prediction = decode_response(response['Body'].read(), freq, prediction_time)

    df_prediction.columns = ['consumption']
    return df_prediction.to_json()
    