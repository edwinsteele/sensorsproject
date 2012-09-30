import logging, os, sys
import defaults

sys.path.append("/Users/esteele/Code/sensorsproject")
os.environ["DJANGO_SETTINGS_MODULE"] = "sensorsproject.settings"

import sensorreadingtransport

logger = logging.getLogger("sensorsproject.udp_receiver")

receiver = sensorreadingtransport.UDPSensorReadingReceiver(defaults.DEFAULT_DESTINATION_HOST,
                                                            defaults.DEFAULT_DESTINATION_PORT)
