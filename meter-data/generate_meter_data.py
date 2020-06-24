import csv, random, json
from datetime import datetime as dt
from datetime import timedelta
from numpy.random import seed
from numpy.random import randint

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

# generate meter id
def get_meter_id():
    numbers = range(1, 10000)
    return random.sample(numbers, 1)[0]

# generate servicePointId - ignored
def get_service_point_id():
    numbers = range(1, 10000)
    return random.sample(numbers, 1)[0]

# generate reading_type
def get_reading_type():
    return 'kWh'

# generate reading quality - ignored
def get_reading_quality():
    return ''

# generate reading time
def get_reading_time():
    return dt.now().strftime('%Y%m%d%H24%M%S')

# generate reading value
def get_reading_value(greaterThan, lessThan):
    digits = 2
    return round(random.uniform(greaterThan, lessThan), digits)

# generate obis code - ignored
def get_obis_code():
    return ''

# generate ansi code - ignored
def get_ansi_code():
    return ''

# generate service multiplier - ignored
def get_service_multiplier():
    return ''

# generate dst flag - ignored
def get_dst_flag():
    return ''

# generate account number
def get_account_number():
    numbers = range(10000000, 90000000)
    return random.sample(numbers, 1)[0]

# generate source quality codes - ignored
def get_source_quality_codes():
    return ''

# get random integer between min and max inclusive
def get_random(min, max):
    return random.randint(min, max+1)

# -------------------------------------------
# Get a random meter read error code
# -------------------------------------------
ERROR_METER_IDS = []
NO_OF_ERROR_RECORDS = 50
ERROR_CODES = [11, 12, 13, 14, 15, 21, 22, 31]

# Initialize list of meter ids for which error records will be generated
def initialize_error_record_generation():
    global ERROR_METER_IDS
    seed(1)
    # generate meter ids for which error record needs to be returned, randomly between meter id
    # 1 and 499 inclusive.
    ERROR_METER_IDS = randint(1, 500, NO_OF_ERROR_RECORDS)
    ERROR_METER_IDS = ERROR_METER_IDS.tolist()
    print("List of meter ids for which error record will exist - {}".format(ERROR_METER_IDS))

# If the given meter_id exist in the error_meter_ids list, return error no. and
# remove that meter id from the error_meter_ids list.
def get_error_code(meter_id):
    global ERROR_METER_IDS
    for i in ERROR_METER_IDS:
        if (meter_id == i):
            ERROR_METER_IDS.remove(meter_id)
            error_code = random.choice(ERROR_CODES)
            print("Error code generated for meter id {} is {}".format(meter_id, error_code))
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
        print("Database file is empty!")
        
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
    
    print("####### Database entries ########")
    print(db)
    print('#################################')
    return db

def save_db(data):
    # Open db file for writing
    fh = open("db.json", 'w')
    json.dump(data, fh)

# load_db()

# -------------------------------------------
# Generate register reads data files
# -------------------------------------------

def generate_records():
    firstdayoftheyear = dt(dt.today().year, 1, 1)
    lastdayoftheyear = dt(dt.today().year, 12, 31)
    start_time = firstdayoftheyear
    end_time = start_time + timedelta(days=1)

    # start_time = dt.now()
    # end_time = dt.now() + timedelta(minutes=60)
    read_interval_minutes = 15
    
    meter_reading_min = 0
    meter_reading_max = 999999999
    meter_reading_max_increment = 50
    meter_reading_min_increment = 5

    
    register_read_type = READING_TYPE['INT'] #kW
    consumption_type = READING_TYPE['AGG'] #kWH

    METER_COUNT = 500

    # load db
    meterlist = load_db(METER_COUNT)

    # Error record generation initialization
    initialize_error_record_generation()

    while start_time <= end_time:
        register_read_rows = []
        consumption_rows = []
        combined_list = []
        error_record_rows = []
        print('Timestamp: '+ start_time.strftime('%Y-%m-%d %H:%M:%S'))
        
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

                print('Meter id: {}, INT register: {}, AGG register: {}, units consumed: {}, last reading: {}, new reading: {}'.format(meter['meter_id'], int_register_list[i], agg_register_list[i], unit_consumed, meter[int_register_list[i]], new_reading_value))
            
                # Add fields into an appropriate list
                # meter_id, register, reading_time, reading_value, reading_type
                register_read_row = [meter['meter_id'], int_register_list[i], start_time.strftime('%Y%m%d%H24%M%S'), new_reading_value, register_read_type]
                register_read_row.extend(CONSTANT_FIELDS)
                consumption_row = [meter['meter_id'], agg_register_list[i], start_time.strftime('%Y%m%d%H24%M%S'), unit_consumed, consumption_type]
                consumption_row.extend(CONSTANT_FIELDS)
                
                # set values in the db
                meter[int_register_list[i]] = new_reading_value
                meter[agg_register_list[i]] = unit_consumed
                
                error_code = get_error_code(meter['meter_id'])
                # If Valid error code is returned, create a error record.
                # Make a record as error record by replacing the register_read_type value to error code,
                # instead of AGG or INT
                if error_code != -1:
                    register_read_row[4] = error_code
                    error_record_rows.append(register_read_row)

                print(register_read_row)
                register_read_rows.append(register_read_row)
                combined_list.append(register_read_row)
                print(consumption_row)
                consumption_rows.append(consumption_row)
                combined_list.append(consumption_row)
        
        print('---------------')
        start_time = start_time + timedelta(minutes=read_interval_minutes)
        # shuffle the rows and write to file
        random.shuffle(register_read_rows)
        write('data/register_reads.csv', register_read_rows)
        write('data/error_register_reads.csv', error_record_rows)
        random.shuffle(consumption_rows)
        write('data/consumption.csv', consumption_rows)
        # shuffle combined records in the list and write to file
        random.shuffle(combined_list)
        write('data/combined_data.csv', combined_list)
        write_in_chunks('data/combined_data.csv', combined_list)

    # write updated readings into meter db
    save_db(meterlist)

#### Uncomment below line to generate meter read records
generate_records()    

# Playing with date times
# print(type(dt.now()))
# firstday = dt(dt.today().year, 1, 1)
# lastday = dt(dt.today().year, 12, 31)
# print(firstday)
# print(lastday)