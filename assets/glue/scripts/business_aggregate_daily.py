import sys
import boto3
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame
from pyspark.sql.functions import *

## @params: [JOB_NAME]
args = getResolvedOptions(sys.argv, ['JOB_NAME', 'db_name', 'business_zone_bucket', 'temp_workflow_bucket'])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# read date information to know which data should be aggregated or re-aggregated
s3 = boto3.resource('s3')
tempDataFile = s3.Object(args['temp_workflow_bucket'], 'glue_workflow_distinct_dates')
dateList = tempDataFile.get()['Body'].read().decode().split(",")

business_zone_bucket_path = "s3://" + args['business_zone_bucket'] + "/aggregated/daily"

if not dateList:
    for dateStr in dateList:
        cleanedMeterDataSource = glueContext.create_dynamic_frame.from_catalog(database = args['db_name'], table_name = "daily", transformation_ctx = "cleanedMeterDataSource", push_down_predicate = "(reading_type == 'INT' and date_str == '{}')".format(dateStr))

        dailyAggregatedIntervalReads = cleanedMeterDataSource.toDF() \
            .groupby('meter_id', 'date_str') \
            .agg(sum("reading_value").alias("SumReadingValue"))

        dailyAggregatedIntervalReads\
          .write\
          .mode("overwrite")\
          .format("parquet")\
          .partitionBy("date_str")\
          .save(business_zone_bucket_path)

job.commit()