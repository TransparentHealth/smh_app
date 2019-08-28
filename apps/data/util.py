from datetime import datetime

import dateparser


def parse_timestamp(timestamp):
    """parse a timestamp string, return a datetime"""
    if timestamp is not None:
        try:
            # fast but fragile
            dt = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S%z')
        except ValueError:
            # slow but reliable
            dt = dateparser.parse(timestamp)
        return dt
