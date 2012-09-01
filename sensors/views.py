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

    def get(self, request, *args, **kwargs):
        earliest_reading = self.get_earliest_reading_time()
        latest_reading = self.get_latest_reading_time()
        recency_readings = SensorReading.objects.filter(datetime_read__gte=earliest_reading, datetime_read__lte=latest_reading)
        if recency_readings:
            most_recent_reading = recency_readings.order_by("-datetime_read")[:1][0]
        else:
            most_recent_reading = None
        logger.debug("most recent reading = %s" % (most_recent_reading,))
        context = { 'one_reading': most_recent_reading, 'reading_context': recency_readings }
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

