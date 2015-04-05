from django.core.management.base import BaseCommand, CommandError
from django_eventbrite.utils import load_event_attendees
from optparse import make_option

class Command(BaseCommand):
    help = 'synchronizes the database with the attendee list'
    args = '<event_id>'

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError("event ID required")
        load_event_attendees(args[0])
