from django.db import models

class Form(models.Model):
    start_longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    start_latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    start_location = models.CharField(max_length=100, blank=True)
    destination_longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    destination_latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    destination_location = models.CharField(max_length=100, blank=True)
    travel_mode = models.CharField(max_length=50, blank=True)
    is_highway = models.BooleanField(default=False)
    distance = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    travel_time = models.TimeField(blank=True, null=True)
    travel_instructions = models.CharField(max_length=1255, blank=True)

    def __str__(self):
        return str(self.distance)
