import os, sys, time

sys.path.append("/Users/esteele/Code/sensorsproject")
os.environ["DJANGO_SETTINGS_MODULE"] = "sensorsproject.settings"

from sensors.models import SensorReading, SensorLocation
import SensorReadingProvider
import serial
#import serial.tools.list_ports

from datetime import datetime
from dateutil.tz import tzlocal

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

# TODO - improve setup process (cmdline args? auto-detect?
# Right USB port
arduino_serial = serial.Serial('/dev/tty.usbmodem411', 38400)
# Left USB port
#arduino_serial = serial.Serial('/dev/tty.usbmodem621', 38400)
srp = SensorReadingProvider.SensorReadingProvider(arduino_serial)

#srp = SensorReadingProvider.SimulatedSensorReadingProvider(None)

latest_humidity_percent = srp.get_latest_humidity()
latest_temperature_celsius = srp.get_latest_temperature()
while latest_humidity_percent is None or latest_temperature_celsius is None:
    print "Bogus value detected on initialisation (t=%s h=%s)" % (latest_temperature_celsius, latest_humidity_percent)
    print "Sleeping for 1s to give sensors time to make a valid reading"
    time.sleep(1)
    latest_humidity_percent = srp.get_latest_humidity()
    latest_temperature_celsius = srp.get_latest_temperature()

while 1:
    latest_humidity_percent = srp.get_latest_humidity()
    latest_temperature_celsius = srp.get_latest_temperature()
    current_datetime_no_secs = datetime.now(tz=tzlocal()).replace(second=0, microsecond=0)
    print "%s: %sc %s%%" % (current_datetime_no_secs, latest_temperature_celsius, latest_humidity_percent)
    SensorReading.objects.create(datetime_read=current_datetime_no_secs,
        temperature_celsius=latest_temperature_celsius,
        humidity_percent=latest_humidity_percent,
        location=lounge_room_sensor)
    wait_until_the_next_minute()

#print SensorReading.objects.all()

