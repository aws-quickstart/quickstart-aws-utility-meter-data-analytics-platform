import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame
from pyspark.sql.functions import *

## @params: [JOB_NAME]
args = getResolvedOptions(sys.argv, ['JOB_NAME', 'db_name', 'business_zone_bucket'])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

cleanedMeterDataSource = glueContext.create_dynamic_frame.from_catalog(database = args['db_name'], table_name = "daily", transformation_ctx = "cleanedMeterDataSource")

dailyAggregatedIntervalReads = cleanedMeterDataSource.toDF() \
    .filter("reading_type = 'INT'") \
    .groupby('meter_id', 'date_str') \
    .agg(sum("reading_value").alias("Sum Reading Value")) 

dfAggregatedReads = DynamicFrame.fromDF(dailyAggregatedIntervalReads, glueContext, "dfAggregatedReads")

business_zone_bucket_path_daily = "s3://" + args['business_zone_bucket'] + "/aggregated/daily"

glueContext.write_dynamic_frame.from_options(frame = dfAggregatedReads, \
    connection_type = "s3", \
    connection_options = {"path": business_zone_bucket_path_daily, "partitionKeys": ["date_str"]},\
    format = "parquet", \
    transformation_ctx = "businessZone")

job.commit()