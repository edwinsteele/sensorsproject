from django.http import HttpResponse
from django.views.generic.base import TemplateView
from sensors.models import SensorReading
import logging

from datetime import datetime, timedelta
from dateutil.tz import tzutc, tzlocal

logger = logging.getLogger(__name__)

def home(request):
    return HttpResponse("Hello, world. You're at the poll index.")

class BaseSensorViewClass(TemplateView):
    template_name = "sensors/one_reading.html"

    def get_earliest_reading_time(self):
        # TODO - need a better default for this
        pass

    def get_latest_reading_time(self):
        return datetime.now(tz=tzutc())

    def get_trend_str(self, readings_in_period):
        """
        Produces a tuple of strings that describe the trend of the data over a recent period. Trend periods:
        < 23 hours of readings: 5 minutes
        < 6d 23h of readings: 1 hour
        > 6d 23h of readings: 1 day
        We assume one reading per minute.

        Initially we'll determine the trend by comparing the last reading with the reading at the start of the trend
        period, but can probably do better than that.

        up 3.2 deg in the past hour
        down 5.3% in the past 5 minutes
        unchanged in the past 5 minutes
        """
        #TODO - Move most of this logic to a manager class. Formatting only here, please.
        READINGS_IN_6D_23H = 9999
        READINGS_IN_23_HOURS = 60 * 23
        READINGS_IN_1_HOUR = 60
        first_sensor_reading = readings_in_period[0]
        latest_sensor_reading = readings_in_period[len(readings_in_period)-1]
        length_of_period = latest_sensor_reading.datetime_read - first_sensor_reading.datetime_read
        if length_of_period < timedelta(hours=23):
            trend_starting_point = latest_sensor_reading.datetime_read - timedelta(minutes=5)
            trend_duration_str = "5 minutes"
        elif length_of_period < timedelta(days=6, hours=23):
            trend_starting_point = latest_sensor_reading.datetime_read - timedelta(hours=1)
            trend_duration_str = "hour"
        else:
            trend_starting_point = latest_sensor_reading.datetime_read - timedelta(days=1)
            trend_duration_str = "day"

        trend_start_sensor_reading = readings_in_period.filter(datetime_read__gte=trend_starting_point)[:1][0]
        temperature_delta = latest_sensor_reading.temperature_celsius - trend_start_sensor_reading.temperature_celsius
        humidity_delta = latest_sensor_reading.humidity_percent - trend_start_sensor_reading.humidity_percent
        return "%s in the last %s" % (temperature_delta, trend_duration_str), \
               "%s in the last %s" % (humidity_delta, trend_duration_str)

    def get(self, request, *args, **kwargs):
        earliest_reading = self.get_earliest_reading_time()
        latest_reading = self.get_latest_reading_time()
        readings_in_period = SensorReading.objects.filter(datetime_read__gte=earliest_reading, datetime_read__lte=latest_reading)
        if readings_in_period:
            most_recent_reading = readings_in_period.order_by("-datetime_read")[:1][0]
            temperature_trend_str, humidity_trend_str = self.get_trend_str(readings_in_period)
        else:
            most_recent_reading = None
            # Not used
            temperature_trend_str = ""
            humidity_trend_str = ""
        logger.debug("most recent reading = %s" % (most_recent_reading,))
        context = { "one_reading": most_recent_reading,
                    "reading_context": readings_in_period,
                    "temperature_trend_str": temperature_trend_str,
                    "humidity_trend_str": humidity_trend_str,}
        return self.render_to_response(context)

class RecentViewClass(BaseSensorViewClass):
    def get_earliest_reading_time(self):
        # Twenty four hours ago
        return datetime.now(tz=tzutc()) - timedelta(days=1)

class LatestViewClass(BaseSensorViewClass):
    # Is this latest as in the most recent one that we have, no matter how old it is, or is it "current"
    def get_earliest_reading_time(self):
        # One hour ago
        return datetime.now(tz=tzutc()) - timedelta(seconds=3600)

class CannedViewClass(BaseSensorViewClass):
    def get_earliest_reading_time(self):
        return datetime(2012, 8, 14, 0, 0, 1, tzinfo=tzlocal())

    def get_latest_reading_time(self):
        return datetime(2012, 8, 14, 23, 59, 59, tzinfo=tzlocal())

