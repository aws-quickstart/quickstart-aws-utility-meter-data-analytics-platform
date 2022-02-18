# MIT No Attribution

# Copyright 2021 Amazon Web Services

# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import boto3
import datetime
import json
import os
import psycopg2
from botocore.exceptions import ClientError

REGION = os.environ['AWS_REGION']
SECRET_NAME = os.environ["SECRET_NAME"]


class JSONDateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        else:
            return json.JSONEncoder.default(self, obj)


def get_sql_statement(requested_aggregation):
    if requested_aggregation == "weekly":
        return """
                select meter_id, year, week_of_year, sum(reading_value) 
                    from daily 
                    where meter_id=%s AND year=%s 
                    group by week_of_year, year, meter_id 
                    order by week_of_year
                """
    elif requested_aggregation == "monthly":
        return """select meter_id, year, month, sum(reading_value) 
                        from daily 
                        where meter_id=%s AND year=%s 
                        group by year, month, meter_id 
                        order by month
            """
    else:
        # make daily the default, or raise an exception
        return "select meter_id, date_str, sum(reading_value) from daily where meter_id=%s AND year=%s group by date_str, meter_id"


def load_redshift_cred():
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=REGION
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=SECRET_NAME
        )

    except ClientError as e:
        raise e
    else:
        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
        else:
            decoded_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])

    return json.loads(secret)


def lambda_handler(event, context):
    dbname = os.environ['Db_schema']
    parameter = event["pathParameters"]

    if ("meter_id" not in parameter) or ("year" not in parameter) or ("requested_aggregation" not in parameter):
        return {
            'statusCode': 500,
            'body': "error: meter_id, year and aggregation type needs to be provided."
        }

    meter_id = parameter["meter_id"]
    year = parameter["year"]
    requested_aggregation = parameter["requested_aggregation"]

    redshift_cred = load_redshift_cred()

    connection = psycopg2.connect(user=redshift_cred["username"],
                                  password=redshift_cred["password"],
                                  host=redshift_cred["host"],
                                  port=redshift_cred["port"],
                                  database=dbname)

    cursor = connection.cursor()

    sql = get_sql_statement(requested_aggregation)

    cursor.execute(sql, (meter_id, year,))
    daily_reads = cursor.fetchall()

    return {
        'statusCode': 200,
        "headers": {
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET"
        },
        'body': json.dumps(daily_reads, cls=JSONDateTimeEncoder)
    }
