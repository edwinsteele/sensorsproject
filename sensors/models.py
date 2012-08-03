from django.db import models
from datetime import datetime
from dateutil.tz import tzlocal
import logging

logger = logging.getLogger(__name__)

class SensorLocation(models.Model):
    location = models.CharField(max_length=40)

    def __unicode__(self):
        return self.location

class SensorReading(models.Model):
    datetime_read = models.DateTimeField('Date and Time of reading', db_index=True)
    temperature_celsius = models.DecimalField(max_digits=3, decimal_places=1)
    humidity_percent = models.DecimalField(max_digits=3, decimal_places=1)
    location = models.ForeignKey(SensorLocation)

    def __unicode__(self):
        return "Reading from sensor %s at %s - temp: %s hum: %s" % \
            (self.location, self.datetime_read, self.temperature_celsius, self.humidity_percent)

    def is_current(self):
        delta = datetime.now(tz=tzlocal()) - self.datetime_read
        logger.debug("Delta seconds = %s" % (delta.seconds,))
        return delta.seconds < 120

    def is_warm(self):
        return self.temperature_celsius > 90

    def compact_date(self):
        return self.datetime_read.strftime("%H:%M %z")

