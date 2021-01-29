#!/usr/bin/env bash

HOME=$(pwd)

functions=(
           "crawler/trigger_glue_crawler" \
           "crawler/get_glue_crawler_state" \
           "redshift/consumption" \
           "ml_pipeline/upload_result"  \
           "ml_pipeline/split_batch"  \
           "ml_pipeline/prepare_training"  \
           "ml_pipeline/prepare_batch"  \
           "meter_forecast" \
           "get_anomaly"  \
           "ml_pipeline/batch_anomaly_detection" \
           "state_topic_subscription" \
           "ml_pipeline/load_pipeline_parameter" \
           "outage_info" \
           "ml_pipeline/check_initial_pipeline_run")

for lambda_folder in ${functions[*]};
do
   function_name=${lambda_folder////_}
   echo $function_name
   (cd $lambda_folder; zip -9qr "$HOME/packages/${function_name}.zip" .;cd $HOME)
done