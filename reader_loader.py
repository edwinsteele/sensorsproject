import random, os, sys

sys.path.append("/Users/esteele/Code/sensorsproject")
os.environ["DJANGO_SETTINGS_MODULE"]="sensorsproject.settings"

from sensors.models import SensorReading, SensorLocation

from decimal import Decimal
from datetime import datetime, timedelta
from dateutil.tz import tzlocal

INITIAL_TEMPERATURE_CELSIUS = Decimal("18.00")
INITIAL_HUMIDITY_PERC = Decimal("85.00")

def sensor_reading_generator(t_celsius, h_percent):
    while True:
        t_celsius += Decimal(str(random.choice((-1,1))/20.0))
        h_percent += Decimal(str(random.choice((-1,1))/20.0))
        yield [t_celsius, h_percent]

lounge_room_sensor=SensorLocation.objects.get(pk=1)
srg = sensor_reading_generator(INITIAL_TEMPERATURE_CELSIUS, INITIAL_HUMIDITY_PERC)
last_temperature_celsius, last_humidity_percent = srg.next()

# We don't want resolution below 1 minute so chop the smaller stuff
last_datetime_read = datetime.now(tz=tzlocal()).replace(second=0, microsecond=0) - timedelta(hours=1)

while last_datetime_read < datetime.now(tz=tzlocal()):
    print "%s: %sc %s%%" % (last_datetime_read, last_temperature_celsius, last_humidity_percent)
    SensorReading.objects.create(datetime_read=last_datetime_read,
        temperature_celsius=last_temperature_celsius,
        humidity_percent=last_humidity_percent,
        location=lounge_room_sensor)
    last_temperature_celsius, last_humidity_percent = srg.next()
    last_datetime_read += timedelta(minutes=1)


#print SensorReading.objects.all()
