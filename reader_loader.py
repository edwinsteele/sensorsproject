import logging
import optparse
from datetime import datetime
from dateutil.tz import tzlocal
import defaults

#import os
#os.environ["DJANGO_SETTINGS_MODULE"] = "sensorsproject.settings"

import sensorreadingprovider
import sensorreadingtransport

logger = logging.getLogger("sensorsproject.reader_loader")

LOUNGE_ROOM_SENSOR_ID = 1

usage_msg = "usage: %prog [options]"
parser = optparse.OptionParser(usage=usage_msg)
parser.add_option("-s", "--sensor",
                  dest="sensor",
                  default=defaults.AUTO_DETERMINE_SENSOR,
                  help="/dev/ttysxxx or auto or simulated")
parser.add_option("-d", "--destination",
                  dest="destination",
                  default=defaults.IN_PROCESS_DESTINATION,
                  help="udp://host[:port] or local for local")

(options, args) = parser.parse_args()
if options.sensor not in  (defaults.ARDUINO_SENSOR_TYPE,
                           defaults.SIMULATED_SENSOR_TYPE,
                           defaults.AUTO_DETERMINE_SENSOR):
    parser.error("sensor-type must be %s or %s" %
                 (defaults.ARDUINO_SENSOR_TYPE, defaults.SIMULATED_SENSOR_TYPE))
if options.destination:
    if options.destination != "local" and options.destination[0:6] != "udp://":
        parser.error("valid destination types are udp://host[:port] or local")


sender = sensorreadingtransport.SensorReadingSenderFactory.\
    sensor_reading_provider_factory_method(options.destination)
reading_provider = sensorreadingprovider.SensorReadingProviderFactory.\
    sensor_reading_provider_factory_method(options.sensor)
reading_provider.initialise()
for latest_temperature_celsius, latest_humidity_percent in reading_provider:
    current_datetime_no_secs = datetime.now(tz=tzlocal()).\
        replace(second=0, microsecond=0)
    logger.debug("%s: Inserting reading... %s: %sc %s%% (count %s)",
                 datetime.now(tz=tzlocal()),
                 current_datetime_no_secs,
                 latest_temperature_celsius,
                 latest_humidity_percent,
                 reading_provider.get_reading_counter())
    sender.send(current_datetime_no_secs, LOUNGE_ROOM_SENSOR_ID,
                latest_temperature_celsius, latest_humidity_percent)
