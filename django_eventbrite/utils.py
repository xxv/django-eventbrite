from django.conf import settings
from django.db import models
from eventbrite import Eventbrite
from .models import Event, TicketType
from decimal import Decimal
from moneyed import Money
import dateutil.parser
import pytz

eb = Eventbrite(settings.EVENTBRITE_OAUTH_TOKEN)

LOCAL_TO_EB_KEY_MAPPING = (
    ('eb_id', 'id'),
    ('eb_url', 'url'),
    ('tickets', 'ticket_classes'),
)

TIME_FIELDS = (
    'end',
    'start',
)

FK_MAP = {
    'tickets': TicketType,
    'events': Event
    }

eb_to_local_map = {}
local_to_eb_map = {}

for kv in LOCAL_TO_EB_KEY_MAPPING:
    eb_to_local_map[kv[1]] = kv[0]
    local_to_eb_map[kv[0]] = kv[1]

def e2l_key(key):
    return eb_to_local_map.get(key, key)
def l2e_key(key):
    return local_to_eb_map.get(key, key)

def e2l_event(event):
    return e2l(Event, event)

def e2l(model, eb_model, save=True):
    existing = model.objects.filter(eb_id=eb_model['id'])
    if existing:
        e = existing[0]
    else:
        e = model(eb_id=eb_model['id'])

    fks = {}

    for eb_key in eb_model.keys():
        loc_key = e2l_key(eb_key)
        if not hasattr(e, loc_key):
            continue
        eb_field = eb_model[eb_key]

        if isinstance(eb_field, dict):
            if 'currency' in eb_field:
                eb_field = Money(Decimal(eb_field['value']) / 100, eb_field['currency'])
            elif 'html' in eb_field:
                eb_field = eb_field['html']
            elif 'timezone' in eb_field:
                tz = pytz.timezone(eb_field['timezone'])
                eb_field = tz.localize(dateutil.parser.parse(eb_field['local']))
            else:
                print("Warning: Unknown complex value type for field %s" % eb_key)
                continue
            setattr(e, loc_key, eb_field)
        elif loc_key in FK_MAP:
            fks[loc_key] = eb_field
        else:
            setattr(e, loc_key, eb_field)
    if save:
        e.save()

    for loc_key, eb_field in fks.items():
        if hasattr(eb_field, '__iter__'):
            for sub_model in eb_field:
                m = e2l(FK_MAP[loc_key], sub_model, save=False)
                getattr(e, loc_key).add(m)
        else:
            m=e2l(FK_MAP[loc_key], eb_field, save=False)
            getattr(e, loc_key).add(m)

    return e

def l2e_event(local):
    if local.eb_id:
        # update
        pass
    else:
        # publish
        pass

def get_next_page_number(pagination):
    if pagination['page_count'] > pagination['page_number']:
        return pagination['page_number'] + 1
    else:
        return None

def load_user_events(**args):
    load_paged_events(eb.get_user_owned_events, **args)

def load_paged_events(method, **args):
    page = 1
    while page:
        print("Loading page %d..." % page)
        response = method(eb.get_user()['id'], page=page, **args)
        events = response['events']
        #import json
        #with open('event_dump', 'w') as dump:
        #    dump.write(json.dumps(events))
        for event in events:
            print("Loading %s..." % event['name']['text'])
            e2l_event(event)
        next_page = get_next_page_number(response['pagination'])
        page = next_page
        if not next_page:
            print("Done loading all pages.")

