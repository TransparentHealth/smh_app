from datetime import datetime

import dateparser
from django.conf import settings


def parse_timestamp(timestamp):
    """parse a timestamp string, return a timezone-aware datetime, 
    in the timezone of settings.TIME_ZONE
    """
    if timestamp is not None:
        try:
            # fast but fragile
            dt = datetime.strptime(timestamp, '%Y-%m-%d T%H:%M:%S%z').strftime('%a %d/%m/%Y %H:%M:%S')
        except ValueError:
            # slow but reliable
            dt = dateparser.parse(
                timestamp,
                settings={
                    'RETURN_AS_TIMEZONE_AWARE': True,
                    'TIMEZONE': settings.TIME_ZONE,
                },
            )

        return dt
