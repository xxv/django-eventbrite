from django.core.management.base import BaseCommand, CommandError
from django_eventbrite.utils import load_user_events
from optparse import make_option

class Command(BaseCommand):
    help = 'synchronizes the database with events'
    option_list = BaseCommand.option_list + (
            make_option('--status', help='only load events matching status'),
            make_option('--order_by', help='order results by'),
            )

    def handle(self, *args, **options):
        desired_options = {}
        if options['status']:
            desired_options['status'] = options['status']
        if options['order_by']:
            desired_options['order_by'] = options['order_by']
        load_user_events(**desired_options)
