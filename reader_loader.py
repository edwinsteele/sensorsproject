import os, sys

sys.path.append("/Users/esteele/Code/sensorsproject")
os.environ["DJANGO_SETTINGS_MODULE"]="sensorsproject.settings"

from django.conf import settings
from sensors.models import SensorReading, SensorLocation

from decimal import Decimal
from datetime import datetime
from dateutil.tz import tzlocal

lounge_room_sensor=SensorLocation.objects.get(pk=1)

SensorReading.objects.create(datetime_read=datetime.now(tz=tzlocal()), \
    temperature_celcius=Decimal("20.01"), \
    humidity_percent=Decimal("92.11"), \
    location=lounge_room_sensor)

print SensorReading.objects.all()
