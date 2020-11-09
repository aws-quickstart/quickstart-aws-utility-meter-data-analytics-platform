import os
import pandas as pd

from pyathena import connect

REGION = os.environ['AWS_REGION']
ATHENA_OUTPUT_BUCKET = os.environ['Athena_bucket']
DB_SCHEMA = os.environ['Db_schema']
USE_WEATHER_DATA = os.environ['With_weather_data']


# expected request: anomaly/{meter_id}?data_start={}&data_end={}&outlier_only={}
def lambda_handler(event, context):

    path_parameter = event["pathParameters"]
    query_parameter = event["queryStringParameters"]

    if ("meter_id" not in path_parameter) \
            or ("data_start" not in query_parameter) \
            or ("data_end" not in query_parameter) \
            or ("outlier_only" not in query_parameter):
        return {
            'statusCode': 500,
            'body': "error: meter_id, data_start, data_end and outlier_only needs to be provided."
        }

    meter_id = path_parameter['meter_id']
    data_start = query_parameter['data_start']
    data_end = query_parameter['data_end']
    outlier_only = query_parameter['outlier_only']

    connection = connect(s3_staging_dir='s3://{}/'.format(ATHENA_OUTPUT_BUCKET), region_name=REGION)

    if USE_WEATHER_DATA == 1:
        query = '''with weather_daily as (
            select date_trunc('day', date_parse(time,'%Y-%m-%d %H:%i:%s')) as datetime,
            avg(temperature) as temperature, avg(apparenttemperature) as apparenttemperature, avg(humidity) as humidity
            from default.weather group by 1
        )
        select ma.*, mw.temperature, mw.apparenttemperature
        from "{}".anomaly ma, weather_daily mw
        where meter_id = '{}'
        and cast(ma.ds as timestamp) >= timestamp '{}' and cast(ma.ds as timestamp) < timestamp '{}'
        and cast(ma.ds as timestamp) = mw.datetime
        '''.format(DB_SCHEMA, DB_SCHEMA, meter_id, data_start, data_end)
    else:
        query = '''
        select * from "{}".anomaly
        where meter_id = '{}'
        and cast(ds as timestamp) >= timestamp '{}' and cast(ds as timestamp) < timestamp '{}'
        '''.format(DB_SCHEMA, meter_id, data_start, data_end)

    if outlier_only == 1:
        query = query + ' and anomaly <> 0'

    df_consumption = pd.read_sql(query, connection)

    return {
        "statusCode": 200,
        "body": df_consumption.to_json()
    }
