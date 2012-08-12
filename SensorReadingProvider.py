import time

__author__ = 'esteele'

import random, re, threading
from decimal import Decimal

class SensorReadingProvider(threading.Thread):
    # 'Humidity: 62.80 %\tTemperature: 20.00 *C\r\n'
    humidity_temp_string_re = re.compile("Humidity: (?P<humidity_perc>[0-9]{1,2}\.[0-9]{2}).*Temperature: (?P<temp_celcius>[0-9]{1,2}\.[0-9]{2}).*$")
    initialisation_re = re.compile("^Initialising DHT Sensor.*")

    def __init__(self, serial_port):
        threading.Thread.__init__(self)
        self.last_humidity_reading = None
        self.last_temperature_reading = None
        self.arduino_serial_port = serial_port
        # Kick off the recorder
        self.start()

    def _record_sensor_reading(self):
        # Goes directly to the sensor and updates class variables
        # TODO - handle when the DHT returns an error (see the arduino source) and return something that can be used upstream to indicate an error
        line = self.arduino_serial_port.readline()
        reading_mo = self.humidity_temp_string_re.match(line)
        init_mo = self.initialisation_re.match(line)
        if reading_mo:
            humidity = reading_mo.group('humidity_perc')
            temperature = reading_mo.group('temp_celcius')
            #print "Matched. Humidity is %s and temp is %s" % (humidity, temperature)
        elif init_mo:
            humidity = temperature = None
            print "Sensor initialisation complete."
        else:
            humidity = temperature = None
            # TODO - fix this handling up a bit
            print "No match for line->%s<-" % (line,)

        self.last_humidity_reading = humidity
        self.last_temperature_reading = temperature

    def is_available(self):
        # TODO - move the initialisation and detection logic here... prob split the serial connected class
        #  so that the simulated sensor doesn't inherit this behaviour
        pass

    def run(self):
       while 1:
           self._record_sensor_reading()

    def get_latest_temperature(self):
        return self.last_temperature_reading

    def get_latest_humidity(self):
        return self.last_humidity_reading


class SimulatedSensorReadingProvider(SensorReadingProvider):
    INITIAL_TEMPERATURE_CELSIUS = Decimal("18.00")
    INITIAL_HUMIDITY_PERC = Decimal("85.00")

    def __init__(self, serial_port):
        self.srg = self._sensor_reading_generator(self.INITIAL_TEMPERATURE_CELSIUS, self.INITIAL_HUMIDITY_PERC)
        SensorReadingProvider.__init__(self, serial_port)

    def _sensor_reading_generator(self, t_celsius, h_percent):
        """
        Generates sensor readings that are relatively stable, moving by + or -0.05 for each calling
        """
        while True:
            t_celsius += Decimal(str(random.choice((-1,1))/20.0))
            h_percent += Decimal(str(random.choice((-1,1))/20.0))
            # Cap humidity at 99% - it'll bork the db otherwise
            h_percent = min(Decimal("99"), h_percent)
            yield [t_celsius, h_percent]

    def _record_sensor_reading(self):
        """
        Simulates a request and response from a sensor, including the time taken to obtain the reading.
        """
        self.last_temperature_reading, self.last_humidity_reading = self.srg.next()
        time.sleep(0.25)

