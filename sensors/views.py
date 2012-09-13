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
    UNCHANGED_STR="Unchanged"

    def get_earliest_reading_time(self):
        pass

    def get_latest_reading_time(self):
        return datetime.now(tz=tzutc())

    def pretty_duration(self, td):
        if td == timedelta(days=1):
            return "day"
        elif td == timedelta(minutes=5):
            return "5 minutes"
        elif td == timedelta(hours=1):
            return "hour"
        else:
            return "some period"

    def pretty_trend(self, trend_decimal):
        """
        Human readable. Takes a float and rounds it up - people don't care about detail to that extent.
        """
        if trend_decimal <= -0.5:
            return "Down %s" % (abs(trend_decimal.to_integral_value()),)
        elif trend_decimal < 0.5:
            return self.UNCHANGED_STR
        elif trend_decimal >= 0.5:
            return "Up %s" % (trend_decimal.to_integral_value(),)

    def get_trend_str(self, trend_duration, temperature_delta, humidity_delta):
        """
        up 3.2 deg in the past hour
        down 5.3% in the past 5 minutes
        unchanged in the past 5 minutes
        """
        temperature_trend_str = self.pretty_trend(temperature_delta)
        humidity_trend_str = self.pretty_trend(humidity_delta)
        # We don't display units if it's unchanged
        if temperature_trend_str == self.UNCHANGED_STR:
            temperature_units = ""
        else:
            temperature_units = "&deg;"

        if humidity_trend_str == self.UNCHANGED_STR:
            humidity_units = ""
        else:
            humidity_units = "%"

        return "%s%s in the last %s" % (temperature_trend_str, temperature_units, self.pretty_duration(trend_duration)),\
               "%s%s in the last %s" % (humidity_trend_str, humidity_units, self.pretty_duration(trend_duration))


    def get(self, request, *args, **kwargs):
        earliest = self.get_earliest_reading_time()
        latest = self.get_latest_reading_time()
        most_recent_reading = SensorReading.objects.most_recent_reading(earliest, latest)
        trend_duration, temperature_delta, humidity_delta = SensorReading.objects.get_trend_data(earliest, latest)
        temperature_trend_str, humidity_trend_str = self.get_trend_str(trend_duration, temperature_delta, humidity_delta)
        readings_in_period = SensorReading.objects.filter(datetime_read__gte=earliest, datetime_read__lte=latest)
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

