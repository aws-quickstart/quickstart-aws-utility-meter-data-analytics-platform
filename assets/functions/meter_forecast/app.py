'''
Testing event
{
  "Athena_bucket": "prediction-pipeline-athenaquerybucket-zz0r25pys2a5",
  "Data_start": "2013-06-01",
  "Data_end": "2014-01-01",
  "Forecast_period": 7,
  "Meter_id": "MAC004534",
  "With_weather_data": 0,
  "ML_endpoint_name": "ml-endpoint-0001"
}
'''

import boto3
import pandas as pd 
import numpy as np
import time
import json
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
    
def encode_request(ts):
    # Todo, Add option for weather data
    instance = {
          "start": str(ts.index[0]),
          "target": [x if np.isfinite(x) else "NaN" for x in ts]    
        }
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
    # we only sent one time series so we only receive one in return
    # however, if possible one will pass multiple time series as predictions will then be faster
    predictions = json.loads(response.decode('utf-8'))['predictions'][0]
    prediction_length = len(next(iter(predictions['quantiles'].values())))
    prediction_index = pd.date_range(start=prediction_time, end=prediction_time + pd.Timedelta(prediction_length-1, unit='H'), freq=freq)
    dict_of_samples = {}
    return pd.DataFrame(data={**predictions['quantiles'], **dict_of_samples}, index=prediction_index)


def lambda_handler(event, context):
    ATHENA_OUTPUT_BUCKET = event['Athena_bucket']
    METER_ID = event['Meter_id']
    ML_ENDPOINT_NAME = event['ML_endpoint_name']
    USE_WEATHER_DATA = event['With_weather_data']
    DATA_START = event['Data_start']
    DATA_END = event['Data_end']
    FORECAST_PERIOD = event['Forecast_period']
    prediction_length = FORECAST_PERIOD * 24

    region = 'us-east-1'
    connection = connect(s3_staging_dir='s3://{}/'.format(ATHENA_OUTPUT_BUCKET), region_name=region)
    query = '''select date_trunc('HOUR', reading_date_time) as datetime, sum(reading_value) as consumption
                from "meter-data".daily 
                where meter_id = '{}' and reading_date_time >= timestamp '{}'
                and  reading_date_time < timestamp '{}'
                group by 1;
                '''.format(METER_ID, DATA_START, DATA_END) 
    result = pd.read_sql(query, connection)
    result = result.set_index('datetime')

    data_kw = result.resample('1H').sum()
    timeseries = data_kw.iloc[:,0]  #np.trim_zeros(data_kw.iloc[:,0], trim='f')
    
    freq = 'H'
    runtime= boto3.client('runtime.sagemaker')
    response = runtime.invoke_endpoint(EndpointName=ML_ENDPOINT_NAME,
                                       ContentType='application/json',
                                       Body=encode_request(timeseries[:]))
    prediction_time = timeseries.index[-1] + pd.Timedelta(1, unit='H')
    df_prediction = decode_response(response['Body'].read(), freq, prediction_time)

    df_prediction.columns = ['consumption']
    #print("return forecast result:", df_prediction)
    return df_prediction.to_json()
    