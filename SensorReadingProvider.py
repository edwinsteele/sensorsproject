import time

__author__ = 'esteele'

import random, re, threading
from decimal import Decimal

class SensorReadingProvider(threading.Thread):
    # 'Humidity: 62.80 %\tTemperature: 20.00 *C\r\n'
    humidity_temp_string_re = re.compile("Humidity: (?P<humidity_perc>[0-9]{1,2}\.[0-9]{2}).*Temperature: (?P<temp_celcius>[0-9]{1,2}\.[0-9]{2}).*$")

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
        mo = self.humidity_temp_string_re.match(line)
        if mo:
            humidity = mo.group('humidity_perc')
            temperature = mo.group('temp_celcius')
            #print "Matched. Humidity is %s and temp is %s" % (humidity, temperature)
        else:
            humidity = temperature = None
            print "No match for line->%s<-" % (line,)

        self.last_humidity_reading = humidity
        self.last_temperature_reading = temperature


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
            yield [t_celsius, h_percent]

    def _record_sensor_reading(self):
        """
        Simulates a request and response from a sensor, including the time taken to obtain the reading.
        """
        self.last_temperature_reading, self.last_humidity_reading = self.srg.next()
        time.sleep(0.25)

