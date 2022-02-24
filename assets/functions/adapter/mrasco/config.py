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

from datetime import datetime, timedelta

mrasco_date_format = "%Y%m%d"
mrasco_datetime_format = "%Y%m%d%H%M%S"
quickstart_date_format = "%Y%m%d%H24%M%S"
mappings = {
    "header": ["meter_id", "obis_code", "reading_time", "reading_value", "error_code", "reading_type"],
    "D0275": {
        "25B": {
            "reading_row": False,
            "parent_record_row": True,
            1: [
                {
                    "field_name": "reading_type",
                    "mapping": lambda x, curr: 'INT'
                },
                {
                    "field_name": "meter_id",
                    "mapping": lambda x, curr: x
                }
            ],
            2: [
                {
                    "field_name": "obis_code",
                    "mapping": lambda x, curr: "3.8.0" if x.startswith("R") else "1.8.0"
                }
            ]
        },
        "26B": {
            "reading_row": False,
            "parent_record_row": False,
            1: [
                {
                    "field_name": "reading_time",
                    "mapping": lambda x, curr:
                    # offset first entry as first time a 30 mins will be added by transformation
                    (datetime.strptime(x, mrasco_date_format) + timedelta(minutes=-30)).strftime(quickstart_date_format)
                }
            ]
        },
        "27B": {
            "reading_row": True,
            "parent_record_row": False,

            2: [
                {
                    "field_name": "reading_value",
                    "mapping": lambda x, curr: x
                },
                {
                    "field_name": "reading_time",
                    "mapping": lambda x, curr:
                    (datetime.strptime(curr, quickstart_date_format) + timedelta(minutes=30)).strftime(
                        quickstart_date_format)
                }
            ],
        }
    },
    "D0010": {
        "026": {
            "reading_row": False,
            "parent_record_row": True,
            1: [
                {
                    "field_name": "reading_type",
                    "mapping": lambda x, curr: 'AGG'
                }
            ],
        },
        "028": {
            "reading_row": False,
            "parent_record_row": False,
            1: [
                {
                    "field_name": "meter_id",
                    "mapping": lambda x, curr: x + "_"
                }
            ],
        },
        "029": {
            "reading_row": True,
            "parent_record_row": False,
            1: [
                {
                    "field_name": "meter_id",
                    "mapping": lambda x, curr: curr[0: curr.index("_")] + x
                }
            ],
            2: [
                {
                    "field_name": "reading_time",
                    "mapping": lambda x, curr:
                    datetime.strptime(x, mrasco_datetime_format).strftime(quickstart_date_format)
                }
            ],
            3: [
                {
                    "field_name": "reading_value",
                    "mapping": lambda x, curr: x
                }
            ],
        }
    }
}
