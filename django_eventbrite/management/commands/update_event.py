from django.core.management.base import BaseCommand, CommandError
from django_eventbrite.utils import update_events

class Command(BaseCommand):
    help = 'synchronizes the database with events'

    def handle(self, *args, **options):
        update_events()
