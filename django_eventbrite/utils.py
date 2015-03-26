from eventbrite import Eventbrite
from models import Event
from django.conf import settings
import dateutil.parser
import pytz

eb = Eventbrite(settings.EVENTBRITE_OAUTH_TOKEN)

LOCAL_TO_EB_KEY_MAPPING = (
    ('eb_id', 'id'),
    ('eb_url', 'url'),
)

EVENT_FIELDS = (
    'description',
    'end',
    'name',
    'start',
    'url',
)

TIME_FIELDS = (
    'end',
    'start',
)

HTML_FIELDS = (
    'description',
    'name',
)

eb_to_local_map = {}
local_to_eb_map = {}

for kv in LOCAL_TO_EB_KEY_MAPPING:
    eb_to_local_map[kv[1]] = kv[0]
    local_to_eb_map[kv[0]] = kv[1]

def eb_to_local(event):
    for field_name in EVENT_FIELDS:
        if field_name in HTML_FIELDS:
            html = event[field_name]['html']
            if hasattr(html, 'rendered'):
                html = html.rendered
            setattr(event, field_name, html)
        elif field_name in TIME_FIELDS:
            tz = pytz.timezone(event[field_name]['timezone'])
            setattr(event, field_name, tz.localize(dateutil.parser.parse(event[field_name]['local'])))
        else:
            setattr(event, field_name, event[field_name])
    print event.name
    event.save()

def update_events():
    events = eb.get_user_owned_events(eb.get_user()['id'])['events']
    for event in events:
        existing = Event.objects.filter(eb_id=event['id'])
        if existing:
            e = existing[0]
        else:
            e = Event(eb_id=event['id'])
        eb_to_local(e)

