from django.db import models

class SensorLocation(models.Model):
    location = models.CharField(max_length=40)

class SensorReading(models.Model):
    datetime_read = models.DateTimeField('Date and Time of reading')
    temperature_celcius = models.DecimalField(max_digits=3, decimal_places=1)
    humidity_percent = models.DecimalField(max_digits=3, decimal_places=1)
    location = models.ForeignKey(SensorLocation)
