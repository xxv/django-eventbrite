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
import traceback

eb = Eventbrite(settings.EVENTBRITE_OAUTH_TOKEN)

LOCAL_TO_EB_KEY_MAPPING = (
    ('eb_id', 'id'),
    ('event', 'event_id'),
    ('eb_url', 'url'),
    ('fee', 'eventbrite_fee'),
    ('tickets', 'ticket_classes'),
    ('canceled', 'cancelled'), # ugh. Their API is inconsistent.
)

TIME_FIELDS = (
    'end',
    'start',
)

SAVE_FIRST = (Event,)

FK_MAP = {
    'tickets': TicketType,
    'event': Event,
    'event_id': Event,
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
        try:
            print("Setting {eb_key!s:<15} to {eb_field!s:<.40} ({eb_key} -> {loc_key})".format(**locals()))
        except:
            print("Error printing debug info")
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
    if type(eb_model) == str:
        existing = model.objects.filter(eb_id=eb_model)
        return existing[0]
    else:
        existing = model.objects.filter(eb_id=eb_model['id'])
    if existing:
        e = existing[0]
        if DEBUG:
            print("Event with ID {0} already in database. Updating.".format(eb_model['id']))
    else:
        e = model(eb_id=eb_model['id'])
        if DEBUG:
            print("Creating new Event with ID {0}".format(eb_model['id']))

    fks = {}

    flatten_fields = FLATTEN.get(eb_model_name)

    for eb_key in eb_model.keys():
        if DEBUG:
            print("Loading eb_key {0}".format(eb_key))
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
                try:
                    print("model {e!s:.<20} has no {loc_key}, skipping...".format(**locals()))
                except Exception:
                    pass
            continue
        e2l_set_local(e, eb_model[eb_key], eb_key, loc_key, fks)

    if save and model in SAVE_FIRST:
        print("Saving...")
        e.save()

    if DEBUG:
        print("Processing foreign key objects")
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
        try:
            e.save()
        except Exception as exc:
            if DEBUG:
                from django.db import connection
                print(connection.queries[-1]['sql'])
            raise exc


    return e

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
                if DEBUG:
                    print("Data: %s" % (obj,))
                    traceback.print_exc()
                else:
                    print("Error loading %s: %s" % (model.__name__, e))
        next_page = get_next_page_number(response['pagination'])
        page = next_page
        if not next_page:
            print("Done loading all pages.")

### stuff to convert back to Eventbrite

def to_multipart(text, html=None):
    result = {}
    result['html'] = html or text
    return result

def to_datetime(when):
    result = {}
    # TODO hardcoded to the TZ of the server because timezones are hard
    result['timezone'] = settings.TIME_ZONE
    result['utc'] = when.astimezone(pytz.utc).isoformat().replace('+00:00', 'Z')

    return result

def to_money(money):
    result = {}
    # Value is in cents
    result['value'] = int(money.amount * 100)
    result['currency'] = money.currency.code
    return result

