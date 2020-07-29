import csv, random, json, os

# global constants
meterdata_filename = 'london_meters.csv'
public_bike_data_filename = 'stations.json'
output_file = 'meter-geo-data.csv'
station_count = 0
meter_count = 0

# load bike data file
with open(public_bike_data_filename) as bike_data_file:
    bike_data = json.load(bike_data_file)
    station_iter = iter(bike_data['stationBeanList'])

# Open output file for writing
out = open(output_file, 'w', newline='')
csv_out = csv.writer(out)

# load london meter data file
with open(meterdata_filename, newline='') as meterids_file:
    reader = csv.reader(meterids_file)
    for row in reader:
        meter_count += 1
        meterid = row[0]
        station = next(station_iter, None)
        if station == None:
            bike_data_file = open(public_bike_data_filename)
            bike_data = json.load(bike_data_file)
            station_iter = iter(bike_data['stationBeanList'])
            station = next(station_iter, None)
        row = (meterid, station['latitude'], station['longitude'])
        print(row)
        csv_out.writerow(row)

print('No of meters {}'.format(meter_count))