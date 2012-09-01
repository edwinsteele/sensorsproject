from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.template.context import RequestContext
from django.views.generic.base import TemplateView
from sensors.models import SensorReading
import logging

from datetime import date, datetime, timedelta
from dateutil.tz import tzutc, tzlocal

logger = logging.getLogger(__name__)

# TODO: Use class-based generic views (https://docs.djangoproject.com/en/dev/topics/class-based-views/generic-display/)

def home(request):
    return HttpResponse("Hello, world. You're at the poll index.")

def year_detail(request, year):
    return HttpResponse("zzzYou're at the year detail for %s." % (year,))

def month_detail(request, year, month):
    return HttpResponse("You're at the month detail for %s/%s" % (month, year))

def day_detail(request, year, month, day):
    try:
        ymd = date(int(year), int(month), int(day))
    except ValueError:
        # Bad date format
        ymd = None
    return HttpResponse("You're at the day detail for %s/%s/%s (%s)." % (day, month, year, ymd))

def generic_detail(request, recency_timedelta):
    # TODO: Make more resilient if there aren't any database objects
    # TODO: is this really the most efficient way to get the most recent reading?
    latest_reading = SensorReading.objects.all().order_by('-datetime_read')[:1][0]
    # Are there any cases where latest reading might not be included in last_hour_readings?
    logger.debug("Processing data starting from: %s" % (recency_timedelta,))
    recency_readings = SensorReading.objects.filter(datetime_read__gte=recency_timedelta)
    return render_to_response('sensors/one_reading.html', {
        'one_reading': latest_reading,
        'reading_context': recency_readings,
        }, context_instance=RequestContext(request))

def recent_detail(request):
    twenty_four_hours_ago = datetime.now(tz=tzutc()) - timedelta(days=1)
    return generic_detail(request, twenty_four_hours_ago)

def latest_detail(request):
    one_hour_ago = datetime.now(tz=tzutc()) - timedelta(seconds=3600)
    return generic_detail(request, one_hour_ago)

class CannedViewClass(TemplateView):
    template_name = "sensors/one_reading.html"

    def get(self, request, *args, **kwargs):
        most_recent_reading = SensorReading.objects.all().order_by('-datetime_read')[:1][0]
        earliest_reading = datetime(2012, 8, 14, 0, 0, 1, tzinfo=tzlocal())
        latest_reading = datetime(2012, 8, 14, 23, 59, 59, tzinfo=tzlocal())
        recency_readings = SensorReading.objects.filter(datetime_read__gte=earliest_reading, datetime_read__lte=latest_reading)
        context = { 'one_reading': most_recent_reading, 'reading_context': recency_readings }
        return self.render_to_response(context)
