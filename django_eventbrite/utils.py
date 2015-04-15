from django.conf import settings
from django.db.models.fields.related import ReverseSingleRelatedObjectDescriptor
from django.db.models.options import FieldDoesNotExist
from eventbrite import Eventbrite
from eventbrite.access_methods import AccessMethodsMixin
from .models import Event, TicketType, Attendee, Order
from decimal import Decimal
from moneyed import Money
import dateutil.parser
import pytz

eb = Eventbrite(settings.EVENTBRITE_OAUTH_TOKEN)

LOCAL_TO_EB_KEY_MAPPING = (
    ('eb_id', 'id'),
    ('eb_url', 'url'),
    ('fee', 'eventbrite_fee'),
    ('tickets', 'ticket_classes'),
    ('canceled', 'cancelled'), # ugh. Their API is inconsistent.
)

TIME_FIELDS = (
    'end',
    'start',
)

FK_MAP = {
    'tickets': TicketType,
    'event': Event,
    'events': Event,
    'attendees': Attendee,
    'order': Order
    }
FLATTEN = {
    'attendees': [
        'profile',
        'costs',
    ]
}

DEBUG = False

eb_to_local_map = {}
local_to_eb_map = {}

for kv in LOCAL_TO_EB_KEY_MAPPING:
    eb_to_local_map[kv[1]] = kv[0]
    local_to_eb_map[kv[0]] = kv[1]

def e2l_key(key):
    return eb_to_local_map.get(key, key)
def l2e_key(key):
    return local_to_eb_map.get(key, key)

def e2l_set_local(obj, eb_field, eb_key, loc_key, fks):
    if DEBUG:
        print("{obj!s:<.20}: Setting {eb_key!s:<15} to {eb_field!s:<.40} ({eb_key} -> {loc_key})".format(**locals()))
    if loc_key in FK_MAP:
        fks[loc_key] = eb_field
        return
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
            return
    setattr(obj, loc_key, eb_field)

def has_field(obj, field):
    return field in obj._meta.get_all_field_names()

def e2l(model, eb_model_name, eb_model, save=True):
    """Loads Eventbrite data into a local model

    The model must have an 'eb_id' field which is unique to that instance.

    This supports converting to special fields, notably:
    * MoneyField
    * DateTimeField

    This also understands Eventbrite's HTML fields, which should map to
    TextFields locally.

    This operates on a single model; just loop for lists.

    If save is not set to True, make sure to save the model yourself,
    otherwise the data will be lost.
    """
    existing = model.objects.filter(eb_id=eb_model['id'])
    if existing:
        e = existing[0]
    else:
        e = model(eb_id=eb_model['id'])

    fks = {}

    flatten_fields = FLATTEN.get(eb_model_name)

    for eb_key in eb_model.keys():
        if flatten_fields and eb_key in flatten_fields:
            if not isinstance(eb_model[eb_key], dict):
                continue
            for k, v in eb_model[eb_key].items():
                loc_key = e2l_key(k)
                if not has_field(e, loc_key):
                    continue
                e2l_set_local(e, v, k, loc_key, fks)
            continue

        loc_key = e2l_key(eb_key)
        if not has_field(e, loc_key):
            if DEBUG:
                print("model {e!s:.<20} has no {loc_key}, skipping...".format(**locals()))
            continue
        e2l_set_local(e, eb_model[eb_key], eb_key, loc_key, fks)

    for loc_key, eb_field in fks.items():
        if isinstance(eb_field, list):
            for sub_model in eb_field:
                m = e2l(FK_MAP[loc_key], loc_key, sub_model, save=False)
                getattr(e, loc_key).add(m)
        else:
            m = e2l(FK_MAP[loc_key], loc_key, eb_field, save=False)
            if isinstance(getattr(model, loc_key), ReverseSingleRelatedObjectDescriptor):
                m.save()
                setattr(e, loc_key, m)
            else:
                getattr(e, loc_key).add(m)

    if save:
        e.save()

    return e

def l2e_event(local):
    if local.eb_id:
        # update
        pass
    else:
        # publish
        pass

def load_user_events(**args):
    load_paged_objects(Event, 'events', eb.get_user_owned_events, 'me', **args)

def load_event(event_id, **args):
    load_single_object(Event, eb.get_event, event_id, **args)

def load_event_attendees(event_id, **args):
    load_paged_objects(Attendee, 'attendees', lambda eb_id, **args: AccessMethodsMixin.get_event_attendees(eb, eb_id, **args), event_id, **args)

def get_next_page_number(pagination):
    if pagination['page_count'] > pagination['page_number']:
        return pagination['page_number'] + 1
    else:
        return None

def load_single_object(model, method, *arg, **args):
    response = method(*arg, **args)
    e2l(model, None, response)

def load_paged_objects(model, key, method, *arg, **args):
    page = 1
    while page:
        print('Loading page %d...' % page)
        args['page'] = page
        response = method(*arg, **args)
        objs = response[key]
        #import json
        #with open('event_dump', 'w') as dump:
        #    dump.write(json.dumps(events))
        for obj in objs:
            ref=obj.get('name', '<#%s>' % obj['id'])
            if isinstance(ref, dict) and 'text' in ref:
                ref = ref['text']
            print('Loading %s %s...' % (model.__name__, ref))
            try:
                e2l(model, key, obj)
            except Exception as e:
                print("Error loading %s: %s" % (ref, e))
        next_page = get_next_page_number(response['pagination'])
        page = next_page
        if not next_page:
            print("Done loading all pages.")

