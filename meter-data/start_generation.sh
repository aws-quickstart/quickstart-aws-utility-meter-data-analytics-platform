#!/bin/bash
now=$(date +%r)
echo "Start time: $now"

for i in $(eval echo {$1..$2})
do
    python3 generate_meter_data.py $i $i &
    sleep 1
done
wait
echo "All processes done!"
now=$(date +%r)
echo "End time: $now"

cd data
aws s3 sync ./ s3://fake-meter-data-partitioned/m$1-$2/