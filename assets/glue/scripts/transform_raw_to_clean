import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame
from pyspark.sql.functions import *

## @params: [JOB_NAME]
args = getResolvedOptions(sys.argv, ['JOB_NAME', 'db_name', 'table_name', 'clean_data_bucket'])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

datasource = glueContext.create_dynamic_frame.from_catalog(database = args['db_name'], table_name = args['table_name'], transformation_ctx = "datasource")
applymapping1 = ApplyMapping.apply(frame = datasource, mappings = [\
    ("col0", "long", "meter_id", "long"), \
    ("col1", "string", "obis_code", "string"), \
    ("col2", "long", "reading_time", "string"), \
    ("col3", "long", "reading_value", "long"), \
    ("col4", "string", "reading_type", "string") \
    ], transformation_ctx = "applymapping1")
    
resolvechoice2 = ResolveChoice.apply(frame = applymapping1, choice = "make_struct", transformation_ctx = "resolvechoice2")

dropnullfields = DropNullFields.apply(frame = resolvechoice2, transformation_ctx = "dropnullfields")

mappedReadings = DynamicFrame.toDF(dropnullfields)

# reading_time could not be passed, so splitting date and time fields manually 
mappedReadings = mappedReadings.withColumn("date_str", col("reading_time").substr(1,8))
mappedReadings = mappedReadings.withColumn("time_str", col("reading_time").substr(9,16))
mappedReadings = mappedReadings.withColumn("time_str", regexp_replace(col("time_str"), "24", ""))

time = to_timestamp(col("time_str"), "HHmmss")
date = to_date(col("date_str"), "yyyyMMdd")

# add separate date and time fields
mappedReadings = mappedReadings.withColumn("week_of_year", weekofyear(date)) \
          .withColumn("day_of_month", dayofmonth(date)) \
          .withColumn("month", month(date)) \
          .withColumn("year", year(date)) \
          .withColumn("hour", hour(time)) \
          .withColumn("minute", minute(time)) 


filteredMeterReads = DynamicFrame.fromDF(mappedReadings, glueContext, "filteredMeterReads")

s3_clean_path = "s3://" + args['clean_data_bucket']

glueContext.write_dynamic_frame.from_options(
    frame = filteredMeterReads,
    connection_type = "s3",    
    connection_options = {"path": s3_clean_path},
    format = "parquet",
    transformation_ctx = "s3CleanDatasink")

job.commit()