# MIT No Attribution

# Copyright 2021 Amazon Web Services

# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import boto3
import csv
import io
import urllib.parse
import os
import config

from datetime import datetime

target_s3_bucket = os.environ['TargetS3Bucket']
target_s3_prefix = os.environ['TargetS3BucketPrefix']
if "DATE_FORMAT" in os.environ:
    config.quickstart_date_format = os.environ['DATE_FORMAT']

mappings = config.mappings
s3 = boto3.client('s3')
flow_file_encoding = 'ascii'
flow_file_line_separator = '|'


def lambda_handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    result_content = [mappings["header_mapping"]] if "header_mapping" in mappings \
        else [mappings["header"]]

    try:
        mrasco_file_response = s3.get_object(Bucket=bucket, Key=key)
        mrasco_file_lines = mrasco_file_response['Body'].read().splitlines()
        header_entries = mrasco_file_lines.pop(0).decode(flow_file_encoding).split(flow_file_line_separator)
        mapping = mappings[next(m for m in mappings if mapping_matches_header(header_entries, m))]

        lines_to_map = len(mrasco_file_lines) - 1
        line_entries = len(mappings["header"])

        i = 0
        current_line = []
        while i < lines_to_map:
            line = mrasco_file_lines[i].decode(flow_file_encoding)
            line_code = line[:3]

            line_mapping = mapping[line_code]

            if line_mapping["parent_record_row"]:
                current_line = ["" for _ in range(line_entries)]

            line_values = line.split(flow_file_line_separator)
            y = 1
            while y < len(line_values):
                if y in line_mapping:
                    current_value = line_values[y]
                    field_mappings = line_mapping[y]
                    for field_mapping in field_mappings:
                        value_index = mappings["header"].index(field_mapping["field_name"])
                        current_line[value_index] = field_mapping["mapping"](current_value, current_line[value_index])
                y += 1

            if line_mapping["reading_row"]:
                result_content.append(current_line)
                current_line = current_line[:]

            i += 1

        output = io.StringIO()
        writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_NONE)
        writer.writerows(result_content)

        output_key = target_s3_prefix + datetime.now().strftime("%Y%m%d-%H%M%S") + ".csv"
        s3.put_object(Bucket=target_s3_bucket, Key=output_key, Body=output.getvalue())
        output.close()

        return {
            "statusCode": 200,
            "body": {
                "result": "s3://{}/{}".format(target_s3_bucket, output_key)
            }
        }

    except Exception as e:
        print(e)
        print('Error with event object {} from bucket {}.'.format(key, bucket))
        raise e


def mapping_matches_header(header_entries, mapping):
    return header_entries[1].upper().startswith(mapping) \
           or header_entries[2].upper().startswith(mapping)
