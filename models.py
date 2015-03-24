from django.db import models

# Create your models here.
class Event(models.Model):
    eb_id = models.IntegerField(unique=True, verbose_name='Eventbrite ID')
    description = models.TextField()
    start = models.DateTimeField()
    end = models.DateTimeField()
    name = models.CharField(max_length=255)
    eb_url = models.URLField(verbose_name='Eventbrite URL')

