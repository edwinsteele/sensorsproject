__author__ = 'esteele'

import re, serial

class SensorReadingProvider:
    # 'Humidity: 62.80 %\tTemperature: 20.00 *C\r\n'
    humidity_temp_string_re = re.compile("Humidity: (?P<humidity_perc>[0-9]{1,2}\.[0-9]{2}).*Temperature: (?P<temp_celcius>[0-9]{1,2}\.[0-9]{2}).*$")

    def __init__(self, serial_port):
        # TODO: Lock access to the hum and temp variables so that they're updated atomically (is that necc?)
        self.last_humidity_reading = None
        self.last_temperature_reading = None
        self.arduino_serial_port = serial_port

    def _read_from_sensor(self):
        # Goes directly to the sensor and updates class variables
        line = self.arduino_serial_port.readline()
        mo = self.humidity_temp_string_re.match(line)
        if mo:
            humidity = mo.group('humidity_perc')
            temp = mo.group('temp_celcius')
            print "Matched. Humidity is %s and temp is %s" % (humidity, temp)
        else:
            humidity = temp = None
            print "No match for line->%s<-" % (line,)

        self.last_humidity_reading = humidity
        self.last_temperature_reading = temp

    def get_latest_temperature(self):
        return self.last_temperature_reading

    def get_latest_humidity(self):
        return self.last_humidity_reading


# Right USB port
arduino_serial = serial.Serial('/dev/tty.usbmodem411', 38400)
# Left USB port
#arduino_serial = serial.Serial('/dev/tty.usbmodem621', 38400)

srp = SensorReadingProvider(arduino_serial)
while 1:
    srp._read_from_sensor()
    humidity = srp.get_latest_humidity()
    temperature = srp.get_latest_temperature()
    print "t: %s, h: %s" % (temperature, humidity)