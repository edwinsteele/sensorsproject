import logging, os, sys

sys.path.append("/Users/esteele/Code/sensorsproject")
os.environ["DJANGO_SETTINGS_MODULE"] = "sensorsproject.settings"

import sensorreadingtransport

logger = logging.getLogger("sensorsproject.reader_loader")

receiver = sensorreadingtransport.UDPSensorReadingReceiver(sensorreadingtransport.UDP_RECEIVER_HOST,
                                                            sensorreadingtransport.UDP_RECEIVER_PORT)
