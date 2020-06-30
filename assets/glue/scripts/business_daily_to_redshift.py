import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

## @params: [TempDir, JOB_NAME]
args = getResolvedOptions(sys.argv, ['TempDir','JOB_NAME', 'db_name', 'redshift_connection', 'temp_workflow_bucket'])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

allDaily = glueContext.create_dynamic_frame.from_catalog(database = args['db_name'], table_name = "daily", transformation_ctx = "allDaily")
glueContext.write_dynamic_frame.from_jdbc_conf(frame = allDaily, catalog_connection = args['redshift_connection'], connection_options = {"dbtable": "daily", "database": args['db_name']}, redshift_tmp_dir = args["TempDir"], transformation_ctx = "allDaily")

# allAggDaily = glueContext.create_dynamic_frame.from_catalog(database = args['db_name'], table_name = "aggregated_daily", transformation_ctx = "allDaily")
# glueContext.write_dynamic_frame.from_jdbc_conf(frame = allAggDaily, catalog_connection = args['redshift_connection'], connection_options = {"dbtable": "aggregated_daily", "database": args['db_name']}, redshift_tmp_dir = args["TempDir"], transformation_ctx = "allAggDaily")

# allAggWeekly = glueContext.create_dynamic_frame.from_catalog(database = args['db_name'], table_name = "aggregated_weekly", transformation_ctx = "allDaily")
# glueContext.write_dynamic_frame.from_jdbc_conf(frame = allAggWeekly, catalog_connection = args['redshift_connection'], connection_options = {"dbtable": "aggregated_weekly", "database": args['db_name']}, redshift_tmp_dir = args["TempDir"], transformation_ctx = "allAggWeekly")

# allAggMonthly = glueContext.create_dynamic_frame.from_catalog(database = args['db_name'], table_name = "aggregated_monthly", transformation_ctx = "allDaily")
# glueContext.write_dynamic_frame.from_jdbc_conf(frame = allAggMonthly, catalog_connection = args['redshift_connection'], connection_options = {"dbtable": "aggregated_monthly", "database": args['db_name']}, redshift_tmp_dir = args["TempDir"], transformation_ctx = "allAggMonthly")

job.commit()