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
        return f'from {self.start_location} to {self.destination_location}'

class User(models.Model):
    current = models.CharField(max_length=100, blank=True)
    start_location = models.CharField(max_length=100, blank=True)
    destination_location = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f'from:{self.start_location}to:{self.destination_location}time:{self.current}'

class appuser(models.Model):
    user = models.CharField(max_length=100, blank=True)
    password = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f'{self.user} {self.password}'
