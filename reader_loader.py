import os, sys, time

sys.path.append("/Users/esteele/Code/sensorsproject")
os.environ["DJANGO_SETTINGS_MODULE"] = "sensorsproject.settings"

from sensors.models import SensorReading, SensorLocation
import SensorReadingProvider


from datetime import datetime
from dateutil.tz import tzlocal

# TODO: Use logging module
# TODO: Improve persistent logging in this script and associated modules to help with diagnosis of arduino probs
def wait_until_the_next_minute():
    """
    We only want to record reading times with one minute accuracy and we don't want to get two
    readings in the same period so we make sure we're not close to the beginning (>0:01s) or to the
    end (<0:59s) just in case we get a little bit of a delay taking the reading.
    """
    t = time.localtime()
    if t.tm_sec < 1:
        time.sleep(61.0)
    elif t.tm_sec < 59:
        time.sleep(59.0)
    else:
        time.sleep(60.0)

lounge_room_sensor = SensorLocation.objects.get(pk=1)
srp = SensorReadingProvider.SensorReadingProviderFactory.sensor_reading_provider_factory_method()
srp.initialise()
while 1:
    # TODO: Perhaps srp's should be generators, that way they can avoid sending a None reading when we've read an
    #  error (can't imagine why we'd get that, but it's possible that we could), and in the same way we can incorporate
    #  the initialisation process, delaying the return of the first valid reading until initialisation is complete
    latest_humidity_percent = srp.get_latest_humidity()
    latest_temperature_celsius = srp.get_latest_temperature()
    current_datetime_no_secs = datetime.now(tz=tzlocal()).replace(second=0, microsecond=0)
    # TODO: Avoid inserting reading when there's already one in the db for that sensor in the same minute
    print "%s: Inserting reading... %s: %sc %s%% (count %s)" % \
          (datetime.now(tz=tzlocal()),
           current_datetime_no_secs,
           latest_temperature_celsius,
           latest_humidity_percent,
            srp.get_reading_counter())
    SensorReading.objects.create(datetime_read=current_datetime_no_secs,
        temperature_celsius=latest_temperature_celsius,
        humidity_percent=latest_humidity_percent,
        location=lounge_room_sensor)
    wait_until_the_next_minute()
