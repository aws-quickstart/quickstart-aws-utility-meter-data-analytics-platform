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
            "new_record_row": False,
            "parent_row": True,
            1: [
                {
                    "field_name": "reading_type",
                    "mapping": lambda x, curr: 'AGG'
                }
            ],
        },
        "028": {
            "new_record_row": True,
            "parent_row": True,
            1: [
                {
                    "field_name": "meter_id",
                    "mapping": lambda x, curr: x + "_"
                }
            ],
        },
        "029": {
            "new_record_row": False,
            "parent_row": False,
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
