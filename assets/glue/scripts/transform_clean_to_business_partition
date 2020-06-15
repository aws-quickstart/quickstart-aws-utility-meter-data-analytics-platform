import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

## @params: [JOB_NAME]
args = getResolvedOptions(sys.argv, ['JOB_NAME', 'db_name', 'table_name', 'business_zone_bucket'])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

cleanedMeterDataSource = glueContext.create_dynamic_frame.from_catalog(database = args['db_name'], table_name = args['table_name'], transformation_ctx = "cleanedMeterDataSource")

#mappedReadings = ApplyMapping.apply(frame = cleanedMeterDataSource, mappings = [\
#    ("meter_id", "long", "meter_id", "long"), \
#    ("obis_code", "string", "obis_code", "string"), \
#    ("reading_time", "string", "reading_time", "string"), \
#    ("reading_value", "long", "reading_value", "long"), \
#    ("reading_type", "string", "reading_type", "string"), \
#    ("date_str", "string", "date_str", "string"), \
#    ("time_str", "string", "time_str", "string"), \
#    ("week_of_year", "int", "week_of_year", "int"), \
#    ("day_of_month", "int", "day_of_month", "int"), \
#    ("month", "int", "month", "int"), \
#    ("year", "int", "year", "int"), \
#    ("hour", "int", "hour", "int"), \
#    ("minute", "int", "minute", "int"), \
#    ], transformation_ctx = "mappedReadings")

mappedReadings = ApplyMapping.apply(frame = cleanedMeterDataSource, mappings = [\
    ("meter_id", "string", "meter_id", "string"), \
    ("obis_code", "string", "obis_code", "string"), \
    ("reading_time", "string", "reading_time", "string"), \
    ("reading_value", "double", "reading_value", "double"), \
    ("reading_type", "string", "reading_type", "string"), \
    ("date_str", "string", "date_str", "string"), \
    ("time_str", "string", "time_str", "string"), \
    ("week_of_year", "int", "week_of_year", "int"), \
    ("day_of_month", "int", "day_of_month", "int"), \
    ("month", "int", "month", "int"), \
    ("year", "int", "year", "int"), \
    ("hour", "int", "hour", "int"), \
    ("minute", "int", "minute", "int"), \
    ], transformation_ctx = "mappedReadings")

business_zone_bucket_path_daily = "s3://" + args['business_zone_bucket'] + "/daily"

businessZone = glueContext.write_dynamic_frame.from_options(frame = mappedReadings, \
    connection_type = "s3", \
    connection_options = {"path": business_zone_bucket_path_daily, "partitionKeys": ["reading_type", "date_str"]},\
    format = "parquet", \
    transformation_ctx = "businessZone")

job.commit()