from django.db import models
from markupfield.fields import MarkupField
from django.utils.html import strip_tags
from django.utils.timezone import localtime

# Create your models here.
class Event(models.Model):
    name = models.CharField(max_length=255)
    eb_id = models.IntegerField(unique=True, verbose_name='Eventbrite ID', null=True)
    eb_url = models.URLField(verbose_name='Eventbrite URL', null=True)
    description = MarkupField()
    start = models.DateTimeField()
    end = models.DateTimeField()

    def __str__(self):
        return " - ".join((strip_tags(self.name), str(localtime(self.start))),)

