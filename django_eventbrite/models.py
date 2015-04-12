from django.db import models
from django.db.models import Sum, Avg, Count
from django.utils.html import strip_tags
from django.utils.timezone import localtime
from djmoney.models.fields import MoneyField
from moneyed import Money

DEFAULT_CURRENCY='USD'

class TicketType(models.Model):
    eb_id = models.BigIntegerField(unique=True, verbose_name='Eventbrite ID')
    name = models.CharField(max_length=255)
    description = models.TextField(null=True)
    cost = MoneyField(max_digits=10, decimal_places=2, default_currency=DEFAULT_CURRENCY)
    fee = MoneyField(max_digits=10, decimal_places=2, default_currency=DEFAULT_CURRENCY)
    donation = models.BooleanField(default=False)
    free = models.BooleanField(default=False)
    event = models.ForeignKey('Event', related_name='tickets')
    quantity_sold = models.IntegerField()

    def __str__(self):
        return self.name

class Order(models.Model):
    eb_id = models.BigIntegerField(unique=True, verbose_name='Eventbrite ID')
    changed = models.DateTimeField()
    created = models.DateTimeField()

class Attendee(models.Model):
    eb_id = models.BigIntegerField(unique=True, verbose_name='Eventbrite ID')
    name = models.CharField(max_length=200)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    quantity = models.PositiveSmallIntegerField()
    cell_phone = models.CharField(max_length=30, blank=True, null=True)
    home_phone = models.CharField(max_length=30, blank=True, null=True)
    work_phone = models.CharField(max_length=30, blank=True, null=True)
    status = models.CharField(max_length=30)
    email = models.EmailField()
    event = models.ForeignKey('Event', related_name='attendees')
    gross = MoneyField(max_digits=10, decimal_places=2, default_currency=DEFAULT_CURRENCY)
    fee = MoneyField(max_digits=10, decimal_places=2, default_currency=DEFAULT_CURRENCY)
    refunded = models.BooleanField(default=False)
    canceled = models.BooleanField(default=False)

class Event(models.Model):
    STATUSES = (
            ('draft', 'draft'),
            ('live', 'live'),
            ('canceled', 'canceled'),
            ('started', 'started'),
            ('ended', 'ended'),
            ('completed', 'completed'),
    )

    name = models.CharField(max_length=255)
    eb_id = models.BigIntegerField(unique=True, verbose_name='Eventbrite ID', null=True)
    eb_url = models.URLField(verbose_name='Eventbrite URL', null=True)
    description = models.TextField(null=True)
    start = models.DateTimeField()
    end = models.DateTimeField()
    capacity = models.IntegerField()
    status = models.CharField(max_length=10, choices=STATUSES)

    def quantity_sold(self):
        result = self.tickets.all().aggregate(Sum('quantity_sold'))
        return result['quantity_sold__sum']
    quantity_sold.short_description='Net sales'

    def quantity_refunded(self):
        return self.attendees.filter(refunded=True).count()
    quantity_refunded.short_description='Refunds'

    def quantity_canceled(self):
        return self.attendees.filter(canceled=True).count()
    quantity_canceled.short_description='Cancellations'

    def ticket_sales(self):
        return sum(map(lambda a: a.gross, self.attendees.filter(refunded=False)), Money(0, 'USD'))
    ticket_sales.short_description='Ticket sales'

    class Meta:
        ordering = ["-end"]

    def __str__(self):
        return " - ".join((strip_tags(self.name), str(localtime(self.start))),)

