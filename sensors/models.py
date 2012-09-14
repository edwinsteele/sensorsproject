from django.db import models
from datetime import datetime, timedelta
from dateutil.tz import tzlocal, tzutc
import logging

logger = logging.getLogger(__name__)

class SensorReadingManager(models.Manager):
    # FIXME - don't forget to factor in the sensor_id!! when doing queries
    def get_trend_data(self, readings_in_period, earliest_reading_time, latest_reading_time):
        """
        Produces a tuple of three values that describe the trend of the data over a recent period. Trend periods:
        < 23 hours of readings: 5 minutes
        < 6d 23h of readings: 1 hour
        > 6d 23h of readings: 1 day
        We assume one reading per minute.

        the tuple elements are:
        1. timedelta object corresponding to the trend period
        2. temperature delta (float) during the trend period
        3. humidity delta (float) during the trend period

        Initially we'll determine the trend by comparing the last reading with the reading at the start of the trend
        period, but can probably do better than that.
        """
        # Get the latest sensor reading first because it fully evaluates the query set, which means the first_sensor_reading
        #  can be served from the cache. If the order is reversed, the slicing places a limit 1 on the query which
        #  means that that the latest_sensor_reading cannot be served from cache
        latest_sensor_reading = readings_in_period[len(readings_in_period)-1]
        first_sensor_reading = readings_in_period[0]
        length_of_period = latest_sensor_reading.datetime_read - first_sensor_reading.datetime_read
        if length_of_period < timedelta(hours=23):
            trend_duration = timedelta(minutes=5)
        elif length_of_period < timedelta(days=6, hours=23):
            trend_duration = timedelta(hours=1)
        else:
            trend_duration = timedelta(days=1)

        trend_starting_point = latest_sensor_reading.datetime_read - trend_duration
        for reading in readings_in_period:
            if reading.datetime_read > trend_starting_point:
                trend_start_sensor_reading = reading
                break
        else:
            # FIXME... BOOM!
            trend_start_sensor_reading = None
        temperature_delta = latest_sensor_reading.temperature_celsius - trend_start_sensor_reading.temperature_celsius
        humidity_delta = latest_sensor_reading.humidity_percent - trend_start_sensor_reading.humidity_percent
        return trend_duration, temperature_delta, humidity_delta


class SensorLocation(models.Model):
    location = models.CharField(max_length=40)

    def __unicode__(self):
        return self.location

class SensorReading(models.Model):
    objects = SensorReadingManager()

    class Meta:
        ordering = ["datetime_read"]

    # datetime_read is stored in the database as UTC
    datetime_read = models.DateTimeField('Date and Time of reading', db_index=True)
    temperature_celsius = models.DecimalField(max_digits=3, decimal_places=1)
    humidity_percent = models.DecimalField(max_digits=3, decimal_places=1)
    location = models.ForeignKey(SensorLocation)

    def __unicode__(self):
        return "Reading from sensor %s at %s - temp: %s hum: %s" % \
            (self.location, self.datetime_read, self.temperature_celsius, self.humidity_percent)

    def is_current(self):
        delta = datetime.now(tz=tzutc()) - self.datetime_read
        return delta.seconds < 120

    def compact_date(self):
        return self.datetime_read.astimezone(tzlocal()).strftime("%H.%M")
