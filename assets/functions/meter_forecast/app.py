'''
Testing event
{
  "version": "2.0",
  "routeKey": "GET /forecast/{meter_id}",
  "rawPath": "/forecast/MAC000002",
  "rawQueryString": "data_start=2013-05-01&data_end=2013-10-01",
  "queryStringParameters": {
    "data_end": "2013-10-01",
    "data_start": "2013-05-01"
  },
  "pathParameters": {
    "meter_id": "MAC000002"
  },
  "isBase64Encoded": false
}
'''

import boto3, os
import pandas as pd
import numpy as np
import json
from pyathena import connect

REGION = os.environ['AWS_REGION']
WORKING_BUCKET = os.environ['WORKING_BUCKET']
ATHENA_OUTPUT_BUCKET = os.environ['Athena_bucket']
DB_SCHEMA = os.environ['Db_schema']
USE_WEATHER_DATA = os.environ['With_weather_data']
DYNAMODB = boto3.resource('dynamodb')
CONFIG_TABLE_NAME = os.environ['config_table']

S3 = boto3.client('s3')
SAGEMAKER = boto3.client('runtime.sagemaker')


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
        "output_types": ["quantiles"],
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
    prediction_index = pd.date_range(start=prediction_time,
                                     end=prediction_time + pd.Timedelta(prediction_length - 1, unit='H'), freq=freq)
    dict_of_samples = {}
    return pd.DataFrame(data={**predictions['quantiles'], **dict_of_samples}, index=prediction_index)


def get_config(name):
    response = DYNAMODB.Table(CONFIG_TABLE_NAME).get_item(
        Key={'name': name}
    )

    return response['Item']["value"]


# expect request: forecast/{meter_id}?ml_endpoint_name={}&data_start={}&data_end={}
def lambda_handler(event, context):
    pathParameter = event["pathParameters"]
    queryParameter = event["queryStringParameters"]

    if ("meter_id" not in pathParameter) \
            or ("data_start" not in queryParameter) \
            or ("data_end" not in queryParameter):
        return {
            'statusCode': 400,
            'body': "error: meter_id, data_start, and data_end needs to be provided."
        }

    meter_id = pathParameter['meter_id']
    ml_endpoint_name = get_config("ML_endpoint_name")
    data_start = queryParameter['data_start']
    data_end = queryParameter['data_end']

    connection = connect(s3_staging_dir='s3://{}/'.format(ATHENA_OUTPUT_BUCKET), region_name=REGION)
    query = '''select date_trunc('HOUR', reading_date_time) as datetime, sum(reading_value) as consumption
                from "{}".daily
                where meter_id = '{}' and reading_date_time >= timestamp '{}'
                and  reading_date_time < timestamp '{}'
                and reading_type = 'INT'
                group by 1;
                '''.format(DB_SCHEMA, meter_id, data_start, data_end)
    result = pd.read_sql(query, connection)
    result = result.set_index('datetime')

    if result.empty:
        # if data frame is empty, return empty object.
        return {
            "statusCode": 200,
            "body": '{"consumption":{}}'
        }

    data_kw = result.resample('1H').sum()
    timeseries = data_kw.iloc[:, 0]  # np.trim_zeros(data_kw.iloc[:,0], trim='f')

    freq = 'H'
    df_weather = None
    if USE_WEATHER_DATA == 1:
        df_weather = get_weather(connection, data_start, DB_SCHEMA)

    response = SAGEMAKER.invoke_endpoint(EndpointName=ml_endpoint_name,
                                       ContentType='application/json',
                                       Body=encode_request(timeseries[:], df_weather))
    prediction_time = timeseries.index[-1] + pd.Timedelta(1, unit='H')
    df_prediction = decode_response(response['Body'].read(), freq, prediction_time)

    df_prediction.columns = ['consumption']
    prediction_result = df_prediction.to_json()

    return {
        "statusCode": 200,
        "body": prediction_result
    }
