import boto3, os, json
import pandas as pd

from pyathena import connect


def lambda_handler(event, context):
    ATHENA_OUTPUT_BUCKET = os.environ['Athena_bucket']
    DB_SCHEMA = os.environ['Db_schema']

    parameter = event
    if "body" in event:
        parameter = json.loads(event["body"])

    METER_ID = parameter['Meter_id']
    DATA_START = parameter['Data_start']
    DATA_END = parameter['Data_end']
    OUTLIER_ONLY = parameter['Outlier_only']

    region = 'us-east-1'
    connection = connect(s3_staging_dir='s3://{}/'.format(ATHENA_OUTPUT_BUCKET), region_name=region)

    query = '''select ma.*, mw.temperature, mw.apparenttemperature 
    from "{}".anomaly ma, "{}".weather_daily mw
    where meter_id = '{}'
    and cast(ma.ds as timestamp) >= timestamp '{}' and cast(ma.ds as timestamp) < timestamp '{}'
    and cast(ma.ds as timestamp) = mw.datetime
    '''.format(DB_SCHEMA, DB_SCHEMA, METER_ID, DATA_START, DATA_END)

    if OUTLIER_ONLY == 1:
        query = query + ' and anomaly <> 0'

    df_consumption = pd.read_sql(query, connection) 
    return df_consumption.to_json()
