import logging
import random
import re
import threading
import time
from decimal import Decimal
import serial
import serial.tools.list_ports
import defaults

logger = logging.getLogger("sensorsproject.sensorreadingprovider")

__author__ = 'esteele'

INITIALISING_STR = "Initialising."


class BaseSensorReadingProvider(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True
        self.last_humidity_reading = None
        self.last_temperature_reading = None
        self.last_diagnostic = INITIALISING_STR
        # Keep track of how many readings we've taken, to help in diagnosing
        #  problems with arduino
        self.reading_counter = 0
        # Kick off the recorder
        self.start()

    def __iter__(self):
        return self

    def next(self):
        # TODO: Perhaps include some checking here to make sure readings are
        #  valid before passing them along
        latest_temperature = self.get_latest_temperature()
        latest_humidity = self.get_latest_humidity()
        return latest_temperature, latest_humidity

    def run(self, *args, **kwargs):
        while 1:
            self._record_sensor_reading()
            self.reading_counter += 1

    def _record_sensor_reading(self):
        # implement in subclass
        pass

    def initialise(self):
        """
        Give the sensor time to initialise and get to a point where it's
        producing a reliable stream of readings
        """
        while self.get_latest_temperature() is None or \
                self.get_latest_humidity() is None:
            logger.info("Waiting for initialisation to complete: %s" %
                        (self.last_diagnostic,))
            logger.info("Sleeping for 1s to give sensors time to make a"
                        " valid reading")
            time.sleep(1)

    def get_latest_temperature(self):
        # It can legitimately be 0, so check it's not None
        if self.last_temperature_reading is not None:
            return self.last_temperature_reading
        else:
            # No need to print error on init
            if self.last_diagnostic != INITIALISING_STR:
                logger.error("Error: Temperature is None. Diag: %s" %
                             (self.last_diagnostic,))

    def get_latest_humidity(self):
        # It can legitimately be 0, so check it's not None
        if self.last_humidity_reading is not None:
            return self.last_humidity_reading
        else:
            # No need to print error during init
            if self.last_diagnostic != INITIALISING_STR:
                logger.error("Error: Humidity is None. Diag: %s" %
                             (self.last_diagnostic,))

    def get_reading_counter(self):
        return self.reading_counter


class ArduinoSensorReadingProvider(BaseSensorReadingProvider):
    # 'Humidity: 62.80 %\tTemperature: 20.00 *C\r\n'
    humidity_temp_string_re = re.compile(
        "Humidity: (?P<humidity_perc>[0-9]{1,2}\.[0-9]{2}).*"
        "Temperature: (?P<temp_celsius>[0-9]{1,2}\.[0-9]{2}).*$")
    initialisation_re = re.compile("^Initialising DHT Sensor.*")

    def __init__(self, serial_port):
        self.arduino_serial_port = serial_port
        BaseSensorReadingProvider.__init__(self)

    def _record_sensor_reading(self):
        # Goes directly to the sensor and updates class variables
        # TODO - handle when the DHT returns an error (see the arduino source)
        #  and return something that can be used upstream to indicate an error
        line = self.arduino_serial_port.readline()
        reading_mo = self.humidity_temp_string_re.match(line)
        init_mo = self.initialisation_re.match(line)
        if reading_mo:
            humidity = reading_mo.group('humidity_perc')
            temperature = reading_mo.group('temp_celsius')
            # Don't unset the last_diagnostic message when we have a successful
            #  reading so that we don't have any race conditions when gathering
            #  readings and diags without locking
            #print "Matched. Hum is %s and temp is %s" % (humidity, temperature)
        elif init_mo:
            humidity = temperature = None
            self.last_diagnostic = "Sensor initialisation complete"
        else:
            humidity = temperature = None
            # TODO - fix this handling up a bit
            self.last_diagnostic = "No match for line->%s<-" % (line.strip(),)

        self.last_humidity_reading = humidity
        self.last_temperature_reading = temperature

    def has_valid_reading(self):
        pass


class SimulatedSensorReadingProvider(BaseSensorReadingProvider):
    INITIAL_TEMPERATURE_CELSIUS = Decimal("18.00")
    INITIAL_HUMIDITY_PERC = Decimal("85.00")

    def __init__(self):
        self.srg = self._sensor_reading_generator(
            self.INITIAL_TEMPERATURE_CELSIUS, self.INITIAL_HUMIDITY_PERC)
        BaseSensorReadingProvider.__init__(self)

    def _sensor_reading_generator(self, t_celsius, h_percent):
        """
        Generates sensor readings that are relatively stable, moving by
         + or -0.05 for each calling
        """
        while True:
            t_celsius += Decimal(str(random.choice((-1, 1)) / 20.0))
            h_percent += Decimal(str(random.choice((-1, 1)) / 20.0))
            # Cap humidity at 99% - it'll bork the db otherwise
            h_percent = min(Decimal("99"), h_percent)
            yield t_celsius, h_percent

    def _record_sensor_reading(self):
        """
        Simulates a request and response from a sensor, including the time
         taken to obtain the reading.
        """
        self.last_temperature_reading, self.last_humidity_reading = \
            self.srg.next()
        time.sleep(0.25)


class SensorReadingProviderFactory(object):
    @staticmethod
    def sensor_reading_provider_factory_method(sensor_str):
        # On my macbook, these physical USB ports exist
        #RIGHT_MACBOOK_USB_PORT="/dev/tty.usbmodem411"
        #LEFT_MACBOOK_USB_PORT="/dev/tty.usbmodem621"
        if sensor_str == defaults.SIMULATED_SENSOR_TYPE:
            logger.debug("Creating provider with simulated sensor type"
                         " as specified")
            srp = SimulatedSensorReadingProvider()

        elif sensor_str == defaults.AUTO_DETERMINE_SENSOR:
            logger.debug("Attempting to auto-detect sensor type")
            logger.debug("Searching for arduino boards ")
            # FIXME - use list_ports.comports() and manually pattern match
            usb_modem_list = list(serial.tools.list_ports.grep(
                ".*tty\.usbmodem[0-9]"))
            if len(usb_modem_list) == 1:
                arduino_port_name, arduino_port_desc, arduino_port_hw = \
                    list(usb_modem_list)[0]
                logger.debug("Found one potential arduino board on %s (%s) with"
                             " hardware type %s" % (arduino_port_name,
                                                    arduino_port_desc,
                                                    arduino_port_hw))
                logger.debug("Assuming it's an Arduino. Connecting at %s baud",
                             defaults.DEFAULT_BAUD)
                arduino_serial = serial.Serial(arduino_port_name,
                                               defaults.DEFAULT_BAUD)
                srp = ArduinoSensorReadingProvider(arduino_serial)

            elif len(usb_modem_list) > 1:
                # TODO: Clean up what we print and do here - include useful
                #  feedback for them so that they can perhaps specify a device
                #  directly
                logger.debug("More than one potential arduino boards. (%s)",
                             usb_modem_list)
                logger.debug("Falling back to Simulated Sensor. Specify a port"
                             " on the commandline to avoid this behaviour")
                srp = SimulatedSensorReadingProvider()

            else:
                logger.debug("No USB-connected Arduino boards. Using Simulated"
                             " Sensor.")
                srp = SimulatedSensorReadingProvider()

        else:
            # A port has been specified
            logger.debug("Attempting to connect to port '%s', as specified,"
                         " at %s baud", sensor_str, defaults.DEFAULT_BAUD)
            arduino_serial = serial.Serial(sensor_str, defaults.DEFAULT_BAUD)
            srp = ArduinoSensorReadingProvider(arduino_serial)

        return srp