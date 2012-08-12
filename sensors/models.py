from django.db import models
from datetime import datetime
from dateutil.tz import tzlocal, tzutc
import logging
import time

logger = logging.getLogger(__name__)

# TODO - make this generic, not just Sydney timezone
seconds_from_UTC = 36000

class SensorLocation(models.Model):
    location = models.CharField(max_length=40)

    def __unicode__(self):
        return self.location

class SensorReading(models.Model):
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
        logger.debug("Delta seconds = %s" % (delta.seconds,))
        return delta.seconds < 120

    def datetime_read_as_seconds_since_epoch_local_tz(self):
        datetime_read_local_tz = self.datetime_read.astimezone(tzlocal())
        logger.debug("datetime_read in local tz: secs since epoch %s. time %s" % \
            (time.mktime(datetime_read_local_tz.timetuple()), datetime_read_local_tz))
        # Rickshaw seems confused about whether something is in UTC or not, so we need to add
        #  the number of seconds from UTC. Meh
        return time.mktime(datetime_read_local_tz.timetuple()) + seconds_from_UTC

    def compact_date(self):
        return self.datetime_read.astimezone(tzlocal()).strftime("%H.%M")

