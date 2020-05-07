### ----------------CIS Data Spec-------------------------------------------
### CustomerID; Name; Zip; Street; City; State; Phone; MeterId
### UUID; String; Number; String; String; String; String; String
### CC81F3BA-6953-4B2D-837A-DFE8F7B82753; John Doe; 98109; 410 Terry Avenue North; Seattle; WA; +1 206 266-7010; 4711
### ------------------------------------------------------------------------
# Reference: https://github.com/chris1610/barnum-proj

import uuid, barnum, json, csv

# load meter DB
def load_db():
    # Open db file and load db in memory
    fh = open("./meter-data/db.json", 'r')
    db = json.load(fh)
    
    return db

# write csv file
def write(filename, row_list):
    with open(filename, 'a', newline='') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerows(row_list)


# generate CIS data file
def generate():
    
    record_list = []
    meter_list = load_db()

    if len(meter_list) == 0:
        print('ERROR - empty file!!!!!!!')
    
    else:
        
        for meter in meter_list:

            # Fullname
            name_tuple = barnum.create_name()
            fullname = name_tuple[0] + ' ' + name_tuple[1]

            # Zip, city, state
            zip_tuple = barnum.create_city_state_zip()
            zipcode = zip_tuple[0]
            city = zip_tuple[1]
            state = zip_tuple[2]

            # House no. and street
            street = barnum.create_street()

            # Phone no.
            phone = barnum.create_phone()

            # create and print cis data record
            cis_data_row = [str(uuid.uuid4()), fullname, zipcode, city, state, street, phone, meter['meter_id']]
            print(cis_data_row)
            record_list.append(cis_data_row)
    
    write('cis_data.csv', record_list)

generate()