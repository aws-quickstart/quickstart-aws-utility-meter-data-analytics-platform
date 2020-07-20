import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

## @params: [TempDir, JOB_NAME]
args = getResolvedOptions(sys.argv, ['TempDir', 'JOB_NAME', 'db_name', 'redshift_connection', 'cis-bucket'])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)
## @type: DataSource
## @args: [database = "meter-data", table_name = "meter_meter_cis_data", transformation_ctx = "datasource0"]
## @return: datasource0
## @inputs: []
datasource0 = glueContext.create_dynamic_frame_from_options("s3",\
                                                          {"paths": ["s3://{}".format(args['cis-bucket'])],"recurse": True},\
                                                           format="csv")

## @type: ApplyMapping
## @args: [mapping = [("col0", "string", "customer_id", "string"), ("col1", "string", "name", "string"), ("col2", "long", "zip", "long"), ("col3", "string", "street", "string"), ("col4", "string", "city", "string"), ("col5", "string", "state", "string"), ("col6", "string", "phone", "string"), ("col7", "long", "meter_id", "long")], transformation_ctx = "applymapping1"]
## @return: applymapping1
## @inputs: [frame = datasource0]
applymapping1 = ApplyMapping.apply(frame = datasource0, mappings = [("col0", "string", "customer_id", "string"), ("col1", "string", "name", "string"), ("col2", "long", "zip", "long"), ("col3", "string", "city", "string"), ("col4", "string", "state", "string"),("col5", "string", "street", "string"),("col6", "string", "phone", "string"),("col7", "string", "meter_id", "string"),("col8", "double", "lat", "double"),("col9", "double", "long", "double")], transformation_ctx = "applymapping1")
## @type: ResolveChoice
## @args: [choice = "make_cols", transformation_ctx = "resolvechoice2"]
## @return: resolvechoice2
## @inputs: [frame = applymapping1]
resolvechoice2 = ResolveChoice.apply(frame = applymapping1, choice = "make_cols", transformation_ctx = "resolvechoice2")
## @type: DropNullFields
## @args: [transformation_ctx = "dropnullfields3"]
## @return: dropnullfields3
## @inputs: [frame = resolvechoice2]
dropnullfields3 = DropNullFields.apply(frame = resolvechoice2, transformation_ctx = "dropnullfields3")
## @type: DataSink
## @args: [catalog_connection = "redshift-cluster-1", connection_options = {"dbtable": "meter_meter_cis_data", "database": "meter-data"}, redshift_tmp_dir = TempDir, transformation_ctx = "datasink4"]
## @return: datasink4
## @inputs: [frame = dropnullfields3]
glueContext.write_dynamic_frame.from_jdbc_conf(frame = dropnullfields3, \
                                               catalog_connection = args['redshift_connection'], \
                                               connection_options = {"dbtable": "cis", "database": args['db_name']}, \
                                               redshift_tmp_dir = args["TempDir"], \
                                               transformation_ctx = "cisData")
job.commit()