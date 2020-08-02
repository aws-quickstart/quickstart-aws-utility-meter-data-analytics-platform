#!/usr/bin/env bash

PWD=`pwd`

functions=("upload_result"  \
           "split_batch"  \
           "prepare_training"  \
           "prepare_batch"  \
           "meter_forecast" \
           "get_anomaly"  \
           "batch_anomaly_detection")

for lambda_folder in ${functions[*]};
do
   zip -9jqr "$PWD/packages/${lambda_folder}.zip" "./${lambda_folder}"
done