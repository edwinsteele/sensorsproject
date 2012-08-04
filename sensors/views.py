from django.shortcuts import render_to_response
from django.http import HttpResponse
from sensors.models import SensorReading

from datetime import date, datetime, timedelta
from dateutil.tz import tzlocal

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

def latest_detail(request):
    """
    stuffs
    """
    # TODO: Make more resilient if there aren't any database objects
    # TODO: is this really the most efficient way to get the most recent reading?
    latest_reading = SensorReading.objects.all().order_by('-datetime_read')[:1][0]
    # Are there any cases where latest reading might not be included in last_hour_readings?
    one_hour_ago = datetime.now(tz=tzlocal()) - timedelta(seconds=3600)
    last_hour_readings = SensorReading.objects.filter(datetime_read__gte=one_hour_ago)
    return render_to_response('sensors/one_reading.html', {
        'one_reading': latest_reading,
        'reading_context': last_hour_readings,
    })
