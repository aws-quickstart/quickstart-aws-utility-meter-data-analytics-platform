import sys
import boto3
from datetime import datetime
from botocore.errorfactory import ClientError
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame
from pyspark.sql.functions import *


def check_if_file_exist(bucket, key):
    s3client = boto3.client('s3')
    fileExists = True
    try:
        s3client.head_object(Bucket=bucket, Key=key)
    except ClientError:
        fileExists = False
        pass

    return fileExists


def move_temp_file(bucket, key):
    dt = datetime.now()
    dt.microsecond

    s3 = boto3.resource('s3')
    newFileName = str(dt.microsecond) + '_' + key
    s3.Object(args['temp_workflow_bucket'], newFileName).copy_from(CopySource="{}/{}".format(bucket, key))
    s3.Object(args['temp_workflow_bucket'], key).delete()


def cleanup_temp_folder(bucket, key):
    if check_if_file_exist(bucket, key):
        move_temp_file(bucket, key)


args = getResolvedOptions(sys.argv, ['JOB_NAME', 'db_name', 'table_name', 'clean_data_bucket', 'temp_workflow_bucket'])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

cleanup_temp_folder(args['temp_workflow_bucket'], 'glue_workflow_distinct_dates')

tableName = args['table_name'].replace("-", "_")
datasource = glueContext.create_dynamic_frame.from_catalog(database = args['db_name'], table_name = tableName, transformation_ctx = "datasource")

applymapping1 = ApplyMapping.apply(frame = datasource, mappings = [("lclid", "string", "meter_id", "string"), \
                                                                    ("datetime", "string", "reading_time", "string"), \
                                                                    ("KWH/hh (per half hour)", "double", "reading_value", "double")], \
                                                                    transformation_ctx = "applymapping1")


resolvechoice2 = ResolveChoice.apply(frame = applymapping1, choice = "make_struct", \
                                     transformation_ctx = "resolvechoice2")

dropnullfields = DropNullFields.apply(frame = resolvechoice2, transformation_ctx = "dropnullfields")

mappedReadings = DynamicFrame.toDF(dropnullfields)

mappedReadings = mappedReadings.withColumn("obis_code", lit(""))
mappedReadings = mappedReadings.withColumn("reading_type", lit("INT"))

reading_time = to_timestamp(col("reading_time"), "yyyy-MM-dd HH:mm:ss")
mappedReadings = mappedReadings \
    .withColumn("week_of_year", weekofyear(reading_time)) \
    .withColumn("date_str", regexp_replace(col("reading_time").substr(1,10), "-", "")) \
    .withColumn("day_of_month", dayofmonth(reading_time)) \
    .withColumn("month", month(reading_time)) \
    .withColumn("year", year(reading_time)) \
    .withColumn("hour", hour(reading_time)) \
    .withColumn("minute", minute(reading_time))

filteredMeterReads = DynamicFrame.fromDF(mappedReadings, glueContext, "filteredMeterReads")

# get the distinct date value and store them in a temp S3 bucket to now which aggregation data need to be
# calculated later on
distinctDates = mappedReadings.select('date_str').distinct().collect()
distinctDatesStrList = ','.join(value['date_str'] for value in distinctDates)

s3 = boto3.resource('s3')
s3.Object(args['temp_workflow_bucket'], 'glue_workflow_distinct_dates').put(Body=distinctDatesStrList)

# write data to S3
filteredMeterReads = DynamicFrame.fromDF(mappedReadings, glueContext, "filteredMeterReads")

s3_clean_path = "s3://" + args['clean_data_bucket']

glueContext.write_dynamic_frame.from_options(
    frame = filteredMeterReads,
    connection_type = "s3",
    connection_options = {"path": s3_clean_path},
    format = "parquet",
    transformation_ctx = "s3CleanDatasink")

job.commit()