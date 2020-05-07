import csv, random, json
from datetime import datetime as dt
from datetime import timedelta

# -------------------------------------------
# Constants / Mappings
# -------------------------------------------

reading_types_map = [
    {'reading_type': 'kWh', 'value_type': 'INTERVAL_DATA'},
    {'reading_type': 'kW', 'value_type': 'INCREMENTAL'}
]

# -------------------------------------------
# FILE WRITER
# -------------------------------------------

# write csv file
def write(filename, row_list):
    with open(filename, 'a', newline='') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerows(row_list)

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
# Meter DB
# -------------------------------------------

def load_db():
    # Open db file and load db in memory
    fh = open("db.json", 'r')
    db = json.load(fh)

    # If db file is empty, generate meterids and write it to db
    if len(db) == 0:
        print("Database file is empty!")
        
        # generate meterids and write it to the file
        meters = []
        meterids = getall_meterids_shuffled(1, 5)
        for mid in meterids:
            meter = {
                'meter_id': mid,
                'meter_reading': 0
            }
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

#load_db()

# -------------------------------------------
# Testing different scenarios
# -------------------------------------------

def test_scenarios():
    meterids = getall_meterids_shuffled(1,6)
    rtime = get_reading_time()
    for mid in meterids:
        print(mid, ';', rtime)

#test_scenarios()

# -------------------------------------------
# MAIN
# -------------------------------------------

# main
def main():
    #print(get_datetime())
    #print(get_reading_value(5.45, 10000.40))
    row = [get_meter_id(), get_service_point_id(), get_reading_type(), get_reading_quality(), get_reading_time(), get_reading_value(5.45, 10000.40), get_obis_code(), get_ansi_code(), get_service_multiplier(), get_dst_flag(), get_account_number(), get_source_quality_codes()]
    print(row)

#main()

def generate_records():
    start_time = dt.now()
    end_time = dt.now() + timedelta(minutes=60)
    read_interval_minutes = 15
    
    meter_reading_min = 0
    meter_reading_max = 100
    meter_reading_max_increment = 50
    meter_reading_min_increment = 5

    register_read_type = 'INT' #kW
    consumption_type = 'AGG' #kWH

    # load db
    meterlist = load_db()

    while start_time <= end_time:
        register_read_rows = []
        consumption_rows = []
        combined_list = []
        print('Timestamp: '+ start_time.strftime('%Y-%m-%d %H:%M:%S'))
        for meter in meterlist:
            unit_consumed = get_random(meter_reading_min_increment, meter_reading_max_increment)
            # increment meter reading value by random increment.
            # reset the value if incrementing the meter reading value makes it go past max value.
            new_reading_value = meter['meter_reading'] + unit_consumed
            if new_reading_value > meter_reading_max:
                new_reading_value = new_reading_value - meter_reading_max

            print('Meter id: {}, units consumed: {}, last reading: {}, new reading: {}'.format(meter['meter_id'], unit_consumed, meter['meter_reading'], new_reading_value))
            
            # Add fields into an appropriate list
            # meter_id, reading_time, reading_value, reading_type
            register_read_row = [meter['meter_id'], start_time.strftime('%Y%m%d%H24%M%S'), new_reading_value, register_read_type]
            consumption_row = [meter['meter_id'], start_time.strftime('%Y%m%d%H24%M%S'), unit_consumed, consumption_type]
            meter['meter_reading'] = new_reading_value

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
        write('register_reads.csv', register_read_rows)
        random.shuffle(consumption_rows)
        write('consumption.csv', consumption_rows)
        # shuffle combined records in the list and write to file
        random.shuffle(combined_list)
        write('combined_data.csv', combined_list)

    # write updated readings into meter db
    save_db(meterlist)
    
generate_records()    
