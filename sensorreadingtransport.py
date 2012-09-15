import socket, SocketServer
import datetime, logging, time
from decimal import Decimal
from sensors.models import SensorReading, SensorLocation
from dateutil.tz import tzoffset

logger = logging.getLogger("sensorsproject.sensorreadingtransport")

# TODO - put this as a CNAME and an SRV record in DNS instead
UDP_RECEIVER_HOST = "localhost"
UDP_RECEIVER_PORT = 59999

class BaseSensorReadingSender(object):
    def __init__(self):
        self.messages_sent = 0
    def send(self, datetime_read, sensor_id, temperature_celsius, humidity_percent):
        pass


class UDPSensorReadingSender(BaseSensorReadingSender):

    def __init__(self, destination_host, destination_port):
        # TODO - gethostbyname if necessary
        self.destination_host = destination_host
        self.destination_port = destination_port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        BaseSensorReadingSender.__init__(self)

    def send(self, datetime_read, sensor_id, temperature_celsius, humidity_percent):
        logger.debug("Sending reading for sensor %s... %s: %sc %s%%" %\
                     (sensor_id, datetime_read, temperature_celsius, humidity_percent))
        # probably better to break datetime_read into seconds since the epoch and another field with tz
        seconds_since_epoch = time.mktime(datetime_read.timetuple())
        utc_offset = datetime_read.utcoffset()
        data = "%s,%s,%s,%s,%s\n" % (sensor_id, seconds_since_epoch, utc_offset, temperature_celsius, humidity_percent)
        self.socket.sendto(data, (self.destination_host, self.destination_port))


class SharedProcessSensorReadingSender(BaseSensorReadingSender):

    def __init__(self, shared_process_receiver):
        self.receiver = shared_process_receiver
        BaseSensorReadingSender.__init__(self)

    def send(self, datetime_read, sensor_id, temperature_celsius, humidity_percent):
        # Pass it straight onto the shared process receiver
        self.receiver.receive(datetime_read, sensor_id, temperature_celsius, humidity_percent)


class BaseSensorReadingReceiver(object):
    def persist(self, datetime_read, sensor_id, temperature_celsius, humidity_percent):
        """
        Persists the newly received reading to the database
        """
        sensor_location = SensorLocation.objects.get(pk=sensor_id)
        logger.debug("Inserting reading for sensor %s... %s: %sc %s%%" %\
            (sensor_id, datetime_read, temperature_celsius, humidity_percent))
        SensorReading.objects.create(datetime_read=datetime_read,
            temperature_celsius=temperature_celsius,
            humidity_percent=humidity_percent,
            location=sensor_location)

    def receive(self, datetime_read, sensor_id, temperature_celsius, humidity_percent):
        pass


class SharedProcessSensorReadingReceiver(BaseSensorReadingReceiver):
    # *args then args in persist?
    def receive(self, sensor_id, datetime_read, temperature_celsius, humidity_percent):
        self.persist(sensor_id, datetime_read, temperature_celsius, humidity_percent)


class UDPSensorReadingReceiver(object):

    class SensorReadingHandler(SocketServer.BaseRequestHandler):
        def handle(self):
            data = self.request[0].strip()
            logger.debug("%s wrote: %s" % (self.client_address[0], data))
            l = data.split(",")
            sensor_id = int(l[0])
            seconds_since_epoch = float(l[1])
            # FIXME - need to parse more than just the hour
            # 10:00:00 or -05:00:00
            utc_offset_in_seconds = int(l[2].partition(":")[0])*60*60
            datetime_read = datetime.datetime.fromtimestamp(seconds_since_epoch, tzoffset(None, utc_offset_in_seconds))
            temperature_celsius = Decimal(l[3])
            humidity_percent = Decimal(l[4])
            self.persist(sensor_id, datetime_read, temperature_celsius, humidity_percent)

        def persist(self, sensor_id, datetime_read, temperature_celsius, humidity_percent):
            """
            Persists the newly received reading to the database
            """
            sensor_location = SensorLocation.objects.get(pk=sensor_id)
            logger.debug("Inserting reading for sensor %s... %s: %sc %s%%" %\
                         (sensor_id, datetime_read, temperature_celsius, humidity_percent))
            SensorReading.objects.create(datetime_read=datetime_read,
                temperature_celsius=temperature_celsius,
                humidity_percent=humidity_percent,
                location=sensor_location)


    def __init__(self, binding_host, binding_port):
        self.binding_host = binding_host
        self.binding_port = binding_port
        server = SocketServer.UDPServer((self.binding_host, self.binding_port), self.SensorReadingHandler)
        server.serve_forever()