import csv, random, json, os
from datetime import datetime as dt
from datetime import timedelta
from numpy.random import seed
from numpy.random import randint
import logging, boto3
from os import listdir
from botocore.config import Config

# -------------------------------------------
# Constants / Mappings
# -------------------------------------------

reading_types_map = [
    {'reading_type': 'kWh', 'value_type': 'INTERVAL_DATA'},
    {'reading_type': 'kW', 'value_type': 'INCREMENTAL'}
]

# unique identifier of each register in a meter
OBIS_CODES = {
    # Registers holding continuous incrementing values
    'INT_REGISTERS': [ '1.8.0', '1.8.1', '1.8.2', '1.8.3' ],
    # Registers holding consumption/aggregate values
    'AGG_REGISTERS': [ '2.8.0', '2.8.1', '2.8.2', '2.8.3' ]
}

READING_TYPE = {
    'AGG': '0.0.0.1.20.1.12.0.0.0.0.0.0.0.0.3.72.1',
    'INT': '0.0.0.1.1.1.12.0.0.0.0.3.0.0.0.3.72.0'
}

# Fields which are constant in each record of data file
# ServicePointID, ReadingQuality, AnsiCode, ServiceMultiplier, DSTflag, AccountNumber, SourceQualityCodes
CONSTANT_FIELDS = [ 'spid', 'rq', 'ansi', 'smult', 'DST', 'AccNum', 'sqcode' ]

# Keep the count of meter read files being generated
METER_READ_FILE_COUNT = 0

# No of records to be saved in each meter read file
NO_OF_RECORDS_PER_FILE = 15000


# -------------------------------------------
# LOGGING SETUP
# -------------------------------------------

# setup logging
log_filename = 'datagen.log'
logging.basicConfig(filename=log_filename,level=logging.INFO,format='%(levelname)s:%(message)s')


# -------------------------------------------
# S3 UPLOAD
# -------------------------------------------
s3 = boto3.resource('s3', region_name='us-east-1')

# upload all objects in a given directory locally, to a given S3 bucket
def upload_to_s3(dir, s3bucket, s3path):
    filenames = listdir(dir)
    for file in filenames:
        logging.debug(file)
        local_file_path = dir + '/' + file
        response = s3.meta.client.upload_file(
            local_file_path, s3bucket, s3path+'/'+file
        )

# -------------------------------------------
# FILE WRITER
# -------------------------------------------

# write csv file
def write(filename, row_list):
    with open(filename, 'a', newline='') as file:
        writer = csv.writer(file, delimiter='|')
        writer.writerows(row_list)

# write in chunks of n rows in 1 file
def write_in_chunks(filename, row_list):
    global NO_OF_RECORDS_PER_FILE
    global METER_READ_FILE_COUNT
    for batch in list(chunks(row_list, NO_OF_RECORDS_PER_FILE)):
        METER_READ_FILE_COUNT += 1
        filename_no_extension = filename.split(".")
        incremental_filename = filename_no_extension[0] + "-" + str(METER_READ_FILE_COUNT) + ".csv"
        write(incremental_filename, batch)

# Yield successive n-sized chunks from lst.
def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

# empty given directory locally
def empty_dir(dirname):
    filenames = listdir(dirname)
    for file in filenames:
        local_file_path = dirname + '/' + file
        os.remove(local_file_path)

# -------------------------------------------
# Functions to generate different values for various fields
# -------------------------------------------

# generate datetime in format YYYYMMDDHH24MMSS
def get_datetime():
    # timestamp=(dt.now() - timedelta(1)).strftime('%Y-%m-%d %H:%M:%S.%f')
    # timestamp=(dt.now()).strftime('%Y-%m-%d %H:%M:%S')
    return dt.now().strftime('%Y%m%d%H24%M%S')

# generate multiple meter ids between a given range and
# return randomly shuffled list of those ids
def getall_meterids_shuffled(low, high):
    meterids = list(range(low, high+1))
    random.shuffle(meterids)
    return meterids

# get random integer between min and max inclusive
def get_random(min, max):
    return random.randint(min, max+1)

# -------------------------------------------
# Get a random meter read error code
# -------------------------------------------
ERROR_METER_IDS = []
ERROR_CODES = [11, 12, 13, 14, 15, 21, 22, 31]
ERROR_START_TIME = dt.fromisoformat('2010-04-20T09:15:00')
ERROR_END_TIME = dt.fromisoformat('2010-04-20T15:25:00')

# Initialize list of meter ids for which error records will be generated, and
# start and end time between which error records needs to be generated.
# meter ids and time, both are inclusive of start and end values
def initialize_error_record_generation(m_start, m_end, start_time, end_time):
    global ERROR_METER_IDS
    global ERROR_START_TIME
    global ERROR_END_TIME
    # set start and end times to the global variables
    ERROR_START_TIME = start_time
    ERROR_END_TIME = end_time
    # add meter ids between starting meter no. (m_start) and ending meter no. (m_end)
    # into the list of error meter ids
    for i in range(m_start, m_end+1):
        ERROR_METER_IDS.append(i)
    logging.debug("List of meter ids for which error record will exist - {}".format(ERROR_METER_IDS))

# If the given meter_id exist in the error_meter_ids list, and
# the given datetime is within error start and end time, then return error no.
def get_error_code(meter_id, current_dt):
    global ERROR_START_TIME
    global ERROR_END_TIME
    global ERROR_METER_IDS

    if ERROR_START_TIME <= current_dt <= ERROR_END_TIME:
        if (meter_id in ERROR_METER_IDS):
            error_code = random.choice(ERROR_CODES)
            logging.debug("Error code generated for meter id {} is {} at {}".format(meter_id, error_code, current_dt))
            return error_code
    return -1

### test generating error records
# initialize_error_record_generation()
# for i in range(0, 500):
#     get_error_code(i)


# -------------------------------------------
# Load (Create or load) Meter DB with given
# no. of meter ids
# -------------------------------------------

def load_db(no_of_meters):
    # Open db file and load db in memory
    fh = open("db.json", 'r')
    db = json.load(fh)

    # If db file is empty, generate meterids and write it to db
    if len(db) == 0:
        logging.debug("Database file is empty!")
        
        # generate meterids and write it to the file
        meters = []
        meterids = getall_meterids_shuffled(1, no_of_meters)
        for mid in meterids:
            meter = {
                'meter_id': mid
            }
            for register_type in OBIS_CODES:
                for register in OBIS_CODES[register_type]:
                    meter[register] = 0
            meters.append(meter)
        
        fh = open("db.json", 'w')
        json.dump(meters, fh)
        db = meters
    
    logging.debug("####### Database entries ########")
    logging.debug(db)
    logging.debug('#################################')
    return db

def save_db(data, filename):
    # Open db file for writing
    fh = open(filename, 'w')
    json.dump(data, fh)

# load_db()

# create meter db file named in the format db-1-599.json,
# where 1 is first meter no. and 599 is last meter no.
def get_meter_db_filename(m1st, mlast):
    return 'db-' + str(m1st) + '-' + str(mlast) + '.json'

def create_db(first_meter_no, last_meter_no):
    # Generate meter records
    logging.debug("Generating meter records from {} to {}".format(first_meter_no, last_meter_no))
    
    # generate meterids and meter records
    meters = []
    meterids = getall_meterids_shuffled(first_meter_no, last_meter_no)
    for mid in meterids:
        meter = {
            'meter_id': mid
        }
        for register_type in OBIS_CODES:
            for register in OBIS_CODES[register_type]:
                meter[register] = 0
        meters.append(meter)
    
    # write meter records in the db file, locally
    db_filename = get_meter_db_filename(first_meter_no, last_meter_no)
    fh = open(db_filename, 'w')
    json.dump(meters, fh)
    db = meters

    logging.debug("####### Database entries ########")
    logging.debug(db)
    logging.debug('#################################')
    return db

# -------------------------------------------
# Generate register reads data files
# -------------------------------------------


def generate_records(first_meter_no, last_meter_no, start_time, end_time, data_dir):
    read_interval_minutes = 15
    
    meter_reading_min = 0
    meter_reading_max = 999999999
    meter_reading_max_increment = 50
    meter_reading_min_increment = 5

    
    register_read_type = READING_TYPE['INT'] #kW
    consumption_type = READING_TYPE['AGG'] #kWH

    # load db
    meterlist = create_db(first_meter_no, last_meter_no)

    while start_time <= end_time:
        register_read_rows = []
        consumption_rows = []
        combined_list = []
        error_record_rows = []
        logging.debug('Timestamp: '+ start_time.strftime('%Y-%m-%d %H:%M:%S'))
        
        for meter in meterlist:
            # Assuming there is 1:1 mapping between INT and AGG registers,
            # get the count of INT registers and generate values for both
            # register types
            int_register_list = OBIS_CODES['INT_REGISTERS']
            agg_register_list = OBIS_CODES['AGG_REGISTERS']
            register_count = len(int_register_list)
            for i in range(0, register_count):
                unit_consumed = get_random(meter_reading_min_increment, meter_reading_max_increment)
                
                # increment register reading value by randomly generated units consumed.
                # reset the value if incrementing the meter reading value makes it go past max value.
                new_reading_value = meter[int_register_list[i]] + unit_consumed
                if new_reading_value > meter_reading_max:
                    new_reading_value = new_reading_value - meter_reading_max

                logging.debug('Meter id: {}, INT register: {}, AGG register: {}, units consumed: {}, last reading: {}, new reading: {}'.format(meter['meter_id'], int_register_list[i], agg_register_list[i], unit_consumed, meter[int_register_list[i]], new_reading_value))
            
                # Add fields into an appropriate list
                # meter_id, register, reading_time, reading_value, reading_type
                register_read_row = [meter['meter_id'], int_register_list[i], start_time.strftime('%Y%m%d%H24%M%S'), new_reading_value, register_read_type]
                register_read_row.extend(CONSTANT_FIELDS)
                consumption_row = [meter['meter_id'], agg_register_list[i], start_time.strftime('%Y%m%d%H24%M%S'), unit_consumed, consumption_type]
                consumption_row.extend(CONSTANT_FIELDS)
                
                # set values in the db
                meter[int_register_list[i]] = new_reading_value
                meter[agg_register_list[i]] = unit_consumed
                
                error_code = get_error_code(meter['meter_id'], start_time)
                # If Valid error code is returned, create a error record.
                # Make a record as error record by replacing the register_read_type value to error code,
                # instead of AGG or INT
                if error_code != -1:
                    register_read_row[4] = error_code
                    error_record_rows.append(register_read_row)

                logging.debug(register_read_row)
                register_read_rows.append(register_read_row)
                combined_list.append(register_read_row)
                logging.debug(consumption_row)
                consumption_rows.append(consumption_row)
                combined_list.append(consumption_row)
        
        logging.debug('---------------')
        start_time = start_time + timedelta(minutes=read_interval_minutes)
        
        # # shuffle the rows and write to file
        # random.shuffle(register_read_rows)
        # write('data/register_reads.csv', register_read_rows)
        # write('data/error_register_reads.csv', error_record_rows)
        # random.shuffle(consumption_rows)
        # write('data/consumption.csv', consumption_rows)
        # # shuffle combined records in the list and write to file
        # random.shuffle(combined_list)
        # write('data/combined_data.csv', combined_list)
        
        # create the filename of the format below
        # [directory]/cd-[meter-no]-[register-read-time].csv
        # e.g. data/cd-34-2020-12-28-03-55-43.csv
        data_filename = data_dir + '/cd-' + str(start_time.strftime('%Y-%m-%d-%H-%M-%S')) + '-M' + str(first_meter_no) + '-M' + str(last_meter_no) + '.csv'
        random.shuffle(combined_list)
        write(data_filename, combined_list)
        # write_in_chunks(data_filename, combined_list)
        logging.info("Finished writing records for meters {} to {} for time {}".format(first_meter_no, last_meter_no, start_time))

    # write updated readings into meter db
    save_db(meterlist, get_meter_db_filename(first_meter_no, last_meter_no))


## ------------- main function orchestrating different function execution ------------- ##
def main():
    
    # set variable for data generation

    # total meter count - make sure this number is fully divisible by batch size i.e.
    # total_meter_count/batch_size shouldn't be a float value. Otherwise some meters
    # will be left without any data generated.
    total_meter_count = 6
    start_date = dt(2010,1,1) #YYYY,MM,DD
    end_date = dt(2010,1,5)

    local_dir = 'data'
    s3bucket = 'fake-meter-data'
    # generate and upload data in a batch size of below
    batch_size = 2

    # Error record generation initialization
    initialize_error_record_generation(2, 3, dt.fromisoformat('2010-01-03T09:15:00'), dt.fromisoformat('2010-01-03T15:25:00'))

    starting_meter_no = 1
    ending_meter_no = starting_meter_no + (batch_size-1)
    while ending_meter_no <= total_meter_count:
        generate_records(starting_meter_no, ending_meter_no, start_date, end_date, local_dir)
        logging.info('Records generated for meter {} to {}'.format(starting_meter_no, ending_meter_no))
        s3path = 'm' + str(starting_meter_no) + '-' + str(ending_meter_no)
        upload_to_s3(local_dir, s3bucket, s3path)
        empty_dir(local_dir)
        
        starting_meter_no = ending_meter_no + 1
        ending_meter_no = ending_meter_no + batch_size

#### Uncomment below line to generate meter read records
main()


# Playing with date times
# logging.debug(type(dt.now()))
# firstday = dt(dt.today().year, 1, 1)
# lastday = dt(dt.today().year, 12, 31)
# logging.debug(firstday)
# logging.debug(lastday)
# upload_to_s3('data', 'fake-meter-data')

    # firstdayoftheyear = dt(dt.today().year, 1, 1)
    # lastdayoftheyear = dt(dt.today().year, 12, 31)
    # start_time = firstdayoftheyear
    # end_time = start_time + timedelta(days=1)
    # end_time = dt(2020,1,2)

    # start_time = dt.now()
    # end_time = dt.now() + timedelta(minutes=60)
    