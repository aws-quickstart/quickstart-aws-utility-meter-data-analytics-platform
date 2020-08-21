import sys
import boto3
import json

from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

create_table_sql = "create table if not exists daily("\
                        "meter_id	        VARCHAR(MAX)    ,   "\
                        "reading_value	    FLOAT8          ,   "\
                        "obis_code	        VARCHAR(32)     , "\
                        "week_of_year	    INT4            , "\
                        "day_of_month	    INT4            , "\
                        "month	            INT4            , "\
                        "year	            INT4            , "\
                        "hour	            INT4            , "\
                        "minute	            INT4            , "\
                        "reading_date_time	timestamp       , "\
                        "reading_type	    VARCHAR(32)     , "\
                        "date_str	        VARCHAR(16)      )"\
                        "DISTKEY(meter_id) SORTKEY(year, meter_id);"

## @params: [TempDir, JOB_NAME]
args = getResolvedOptions(sys.argv, ['TempDir','JOB_NAME', 'db_name', 'redshift_connection', 'temp_workflow_bucket'])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

allDaily = glueContext.create_dynamic_frame.from_catalog(database = args['db_name'], table_name = "daily", transformation_ctx = "allDaily")
glueContext.write_dynamic_frame.from_jdbc_conf(frame = allDaily, catalog_connection = args['redshift_connection'], connection_options = {"preactions":create_table_sql, "dbtable": "daily", "database": args['db_name']}, redshift_tmp_dir = args["TempDir"], transformation_ctx = "allDaily")

# allAggDaily = glueContext.create_dynamic_frame.from_catalog(database = args['db_name'], table_name = "aggregated_daily", transformation_ctx = "allDaily")
# glueContext.write_dynamic_frame.from_jdbc_conf(frame = allAggDaily, catalog_connection = args['redshift_connection'], connection_options = {"dbtable": "aggregated_daily", "database": args['db_name']}, redshift_tmp_dir = args["TempDir"], transformation_ctx = "allAggDaily")

# allAggWeekly = glueContext.create_dynamic_frame.from_catalog(database = args['db_name'], table_name = "aggregated_weekly", transformation_ctx = "allDaily")
# glueContext.write_dynamic_frame.from_jdbc_conf(frame = allAggWeekly, catalog_connection = args['redshift_connection'], connection_options = {"dbtable": "aggregated_weekly", "database": args['db_name']}, redshift_tmp_dir = args["TempDir"], transformation_ctx = "allAggWeekly")

# allAggMonthly = glueContext.create_dynamic_frame.from_catalog(database = args['db_name'], table_name = "aggregated_monthly", transformation_ctx = "allDaily")
# glueContext.write_dynamic_frame.from_jdbc_conf(frame = allAggMonthly, catalog_connection = args['redshift_connection'], connection_options = {"dbtable": "aggregated_monthly", "database": args['db_name']}, redshift_tmp_dir = args["TempDir"], transformation_ctx = "allAggMonthly")

job.commit()