import logging, os, sys, time
from datetime import datetime
from dateutil.tz import tzlocal

sys.path.append("/Users/esteele/Code/sensorsproject")
os.environ["DJANGO_SETTINGS_MODULE"] = "sensorsproject.settings"

import sensorreadingprovider, sensorreadingtransport

logger = logging.getLogger("sensorsproject.reader_loader")

LOUNGE_ROOM_SENSOR_ID=1

# TODO: Improve persistent logging in this script and associated modules to help with diagnosis of arduino problems
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

#receiver = sensorreadingtransport.SharedProcessSensorReadingReceiver()
#sender = sensorreadingtransport.SharedProcessSensorReadingSender(receiver)
sender = sensorreadingtransport.UDPSensorReadingSender(sensorreadingtransport.UDP_RECEIVER_HOST,
                                                        sensorreadingtransport.UDP_RECEIVER_PORT)
srp = sensorreadingprovider.SensorReadingProviderFactory.sensor_reading_provider_factory_method(throttle_time_secs=60)
srp.initialise()
for latest_temperature_celsius, latest_humidity_percent in srp:
    current_datetime_no_secs = datetime.now(tz=tzlocal()).replace(second=0, microsecond=0)
    logger.debug("%s: Inserting reading... %s: %sc %s%% (count %s)" %\
                 (datetime.now(tz=tzlocal()),
                  current_datetime_no_secs,
                  latest_temperature_celsius,
                  latest_humidity_percent,
                  srp.get_reading_counter()))
    sender.send(current_datetime_no_secs, LOUNGE_ROOM_SENSOR_ID, latest_temperature_celsius, latest_humidity_percent)
    wait_until_the_next_minute()
