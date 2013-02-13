import socket
import SocketServer
import datetime
import logging
import time
import urlparse
from decimal import Decimal

from dateutil.tz import tzoffset

from sensors.models import SensorReading, SensorLocation
import defaults


logger = logging.getLogger("sensorsproject.sensorreadingtransport")


class BaseSensorReadingSender(object):
    def __init__(self):
        self.messages_sent = 0

    def _do_send(self, datetime_read, sensor_id, temp_celsius, humidity_perc):
        pass

    def send(self, *args, **kwargs):
        """
        We only want to record reading times with one minute accuracy and we
         don't want to get two readings in the same period so we make sure
         we're not close to the beginning (>0:01s) or to the end (<0:59s) just
         in case we get a little bit of a delay taking the reading.

        Note that we take the time before we do the send call, otherwise
         we're gradually skewing our reading period by the duration of the
          send (which we need to assume can be non-trivial)
        """
        t = time.localtime()
        self._do_send(*args, **kwargs)
        if t.tm_sec < 1:
            sleep_time = 61.0
        elif t.tm_sec < 59:
            sleep_time = 59.0
        else:
            sleep_time = 60.0

        logger.debug("Send complete. Sleeping for %s seconds" % (sleep_time,))
        time.sleep(sleep_time)


class UDPSensorReadingSender(BaseSensorReadingSender):

    def __init__(self, destination_host, destination_port):
        # TODO - gethostbyname if necessary
        self.destination_host = destination_host
        self.destination_port = destination_port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        BaseSensorReadingSender.__init__(self)

    def _do_send(self, datetime_read, sensor_id, temp_celsius, humidity_perc):
        logger.debug("Sending reading for sensor %s... %s: %sc %s%%",
                     sensor_id,
                     datetime_read,
                     temp_celsius,
                     humidity_perc)
        # probably better to break datetime_read into seconds since the epoch
        #  and another field with tz
        seconds_since_epoch = time.mktime(datetime_read.timetuple())
        utc_offset = datetime_read.utcoffset()
        data = "%s,%s,%s,%s,%s\n" % (sensor_id,
                                     seconds_since_epoch,
                                     utc_offset,
                                     temp_celsius,
                                     humidity_perc)
        self.socket.sendto(data, (self.destination_host, self.destination_port))


class SharedProcessSensorReadingSender(BaseSensorReadingSender):

    def __init__(self, shared_process_receiver):
        self.receiver = shared_process_receiver
        BaseSensorReadingSender.__init__(self)

    def _do_send(self, datetime_read, sensor_id, temp_celsius, humidity_perc):
        # Pass it straight onto the shared process receiver
        self.receiver.receive(
            datetime_read, sensor_id, temp_celsius, humidity_perc)


class SensorReadingSenderFactory(object):
    @staticmethod
    def sensor_reading_provider_factory_method(destination_str):
        u = urlparse.urlsplit(destination_str)
        if destination_str.lower() == defaults.IN_PROCESS_DESTINATION:
            # Given this is in-process, we need to create a receiver too as
            #  a part of constructing the sender
            sender = SharedProcessSensorReadingSender(
                SharedProcessSensorReadingReceiver())
        # urlsplit does an implicit tolower() on the scheme
        elif u.scheme == defaults.UDP_TRANSPORT_TYPE:
            if u.port:
                dport = u.port
            else:
                dport = defaults.DEFAULT_DESTINATION_PORT
            sender = UDPSensorReadingSender(u.hostname, dport)
        else:
            # FIXME - is this the right behaviour, or raise an exception?
            sender = None

        return sender


class BaseSensorReadingReceiver(object):
    def persist(self, datetime_read, sensor_id, temp_celsius, humidity_perc):
        """
        Persists the newly received reading to the database
        """
        sensor_location = SensorLocation.objects.get(pk=sensor_id)
        logger.debug("Inserting reading for sensor %s... %s: %sc %s%%",
                     sensor_id, datetime_read, temp_celsius, humidity_perc)
        SensorReading.objects.create(datetime_read=datetime_read,
                                     temp_celsius=temp_celsius,
                                     humidity_perc=humidity_perc,
                                     location=sensor_location)

    def receive(self, datetime_read, sensor_id, temp_celsius, humidity_perc):
        pass


class SharedProcessSensorReadingReceiver(BaseSensorReadingReceiver):
    def receive(self, sensor_id, datetime_read, temp_celsius, humidity_perc):
        self.persist(sensor_id, datetime_read, temp_celsius, humidity_perc)


class UDPSensorReadingReceiver(object):
    # Do we want throttling here too, in case the arduino sends through
    #  readings too frequently?

    class SensorReadingHandler(SocketServer.BaseRequestHandler,
                               BaseSensorReadingReceiver):
        def extract_values_from_data(self, data):
            """
            parses the reading sent over the wire into values that can be put
             into the database.

            The data contains the following fields:
            0: sensor_id
            1: seconds since the epoch as a float, or None, if the receiving
                timestamp is to be used.
            2: timezone e.g. 10:00:00 or -05:00:00 or None if the receiving
                timezone is to be used.
            3. temperature reading as a float
            4. humidity reading as a float

            Note that the arduino boards will not necessarily have a clock,
             so will not always be able to provide a reading timestamp, so we
            take a timestamp where we can get it.
            """
            l = data.split(",")
            sensor_id = int(l[0])
            seconds_since_epoch = float(l[1])
            # FIXME - need to parse more than just the hour
            utc_offset_in_seconds = int(l[2].partition(":")[0]) * 60 * 60
            reading_datetime = datetime.datetime.fromtimestamp(
                seconds_since_epoch, tzoffset(None, utc_offset_in_seconds))
            temp_celsius = Decimal(l[3])
            humidity_perc = Decimal(l[4])
            return reading_datetime, sensor_id, temp_celsius, humidity_perc

        def handle(self):
            data = self.request[0].strip()
            logger.debug("%s wrote: %s" % (self.client_address[0], data))
            self.persist(*self.extract_values_from_data(data))

    def __init__(self, binding_host, binding_port):
        self.binding_host = binding_host
        self.binding_port = binding_port
        server = SocketServer.UDPServer((self.binding_host, self.binding_port),
                                        self.SensorReadingHandler)
        server.serve_forever()