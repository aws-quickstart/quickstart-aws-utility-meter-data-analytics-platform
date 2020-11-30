import json
import sys
from datetime import datetime

import boto3
from awsglue.context import GlueContext
from awsglue.dynamicframe import DynamicFrame
from awsglue.job import Job
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from botocore.errorfactory import ClientError
from pyspark.context import SparkContext
from pyspark.sql.functions import *
from pyspark.sql.functions import *
from pyspark.sql.types import *

s3_resource = boto3.resource('s3')


def check_if_file_exist(bucket, key):
    s3client = boto3.client('s3')
    file_exists = True
    try:
        s3client.head_object(Bucket=bucket, Key=key)
    except ClientError:
        file_exists = False
        pass

    return file_exists


def move_temp_file(bucket, key):
    dt = datetime.now()
    dt.microsecond

    new_file_name = str(dt.microsecond) + '_' + key
    s3_resource.Object(args['temp_workflow_bucket'], new_file_name).copy_from(CopySource="{}/{}".format(bucket, key))
    s3_resource.Object(args['temp_workflow_bucket'], key).delete()


def cleanup_temp_folder(bucket, key):
    if check_if_file_exist(bucket, key):
        move_temp_file(bucket, key)


def is_first_run():
    """
    Checks if the number of job runs for this job is 0.

    TODO: check if at least one successful job is in the

    :return: True if this is the first job run
    """

    client = boto3.client('glue', region_name=args["region"])
    runs = client.get_job_runs(
        JobName=args["JOB_NAME"],
        MaxResults=1
    )

    # return len(runs["JobRuns"]) == 0
    return True  # TODO currently only first run is supported


def write_job_state_information(readings):
    """
     get the distinct date value and store them in a temp S3 bucket to now which aggregation data need to be
     calculated later on
    """
    distinct_dates = readings.select('date_str').distinct().collect()
    distinct_dates_str_list = list(value['date_str'] for value in distinct_dates)

    state = {
        "dates": distinct_dates_str_list,
        "first_run": is_first_run()
    }

    s3_resource.Object(args['temp_workflow_bucket'], 'glue_workflow_distinct_dates').put(Body=json.dumps(state))


def parse_date_string(timestamp_str):
    return datetime.strptime(timestamp_str, "%Y%m%d%H24%M%S")


args = getResolvedOptions(sys.argv,
                          ['JOB_NAME', 'db_name', 'table_name', 'clean_data_bucket', 'temp_workflow_bucket', 'region'])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

cleanup_temp_folder(args['temp_workflow_bucket'], 'glue_workflow_distinct_dates')

tableName = args['table_name'].replace("-", "_")
datasource = glueContext.create_dynamic_frame.from_catalog(database=args['db_name'], table_name=tableName,
                                                           transformation_ctx="datasource")

datasource = datasource.resolveChoice(specs = [('col3','make_cols')])

mapped_readings = ApplyMapping.apply(frame=datasource, mappings=[ \
    ("col0", "long", "meter_id", "string"), \
    ("col1", "string", "obis_code", "string"), \
    ("col2", "long", "reading_time", "string"), \
    ("col3_double", "double", "reading_value", "double"), \
    ("col3_string", "string", "error_value", "string"), \
    ("col4", "string", "reading_type", "string") \
    ], transformation_ctx="mapped_readings")

df_readings = DynamicFrame.toDF(mapped_readings)

# reading_time could not be passed, so splitting date and time fields manually
df_readings = df_readings.withColumn("date_str", col("reading_time").substr(1, 8))

timeStr = regexp_replace(col("reading_time").substr(9, 16), "24", "")
time = to_timestamp(timeStr, "HHmmss")
date = to_date(col("date_str"), "yyyyMMdd")

udfParseDateString = udf(parse_date_string, TimestampType())

# add separate date and time fields
df_readings = df_readings.withColumn("week_of_year", weekofyear(date)) \
    .withColumn("day_of_month", dayofmonth(date)) \
    .withColumn("month", month(date)) \
    .withColumn("year", year(date)) \
    .withColumn("hour", hour(time)) \
    .withColumn("minute", minute(time)) \
    .withColumn("reading_date_time", udfParseDateString("reading_time")) \
    .drop("reading_time")

# write data to S3
filteredMeterReads = DynamicFrame.fromDF(df_readings, glueContext, "filteredMeterReads")

s3_clean_path = "s3://" + args['clean_data_bucket']

glueContext.write_dynamic_frame.from_options(
    frame=filteredMeterReads,
    connection_type="s3",
    connection_options={"path": s3_clean_path},
    format="parquet",
    transformation_ctx="s3CleanDatasink")

write_job_state_information(df_readings)

job.commit()
