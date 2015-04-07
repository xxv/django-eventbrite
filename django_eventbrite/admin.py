from django.contrib import admin

from .models import Event, TicketType, Attendee

class TicketTypeInline(admin.StackedInline):
    model = TicketType
    readonly_fields = (
        'eb_id',
        'event',
    )

@admin.register(Attendee)
class AttendeeAdmin(admin.ModelAdmin):
    search_fields = (
        'first_name',
        'last_name',
    )

    readonly_fields = (
        'eb_id',
        'event',
    )

    list_display = (
        'first_name',
        'last_name',
        'email',
        'cell_phone',
        'quantity',
        'gross',
        'status',
    )

    list_filter = (
        ('status',)
    )

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    search_fields = (
            'name',
            'description',
            'eb_id',
    )

    readonly_fields = (
        'eb_id',
        'eb_url',
    )

    list_display = (
        'name',
        'start',
        'end',
        'status',
        'capacity',
        'ticket_sales',
        'quantity_sold',
        'quantity_refunded',
        'quantity_canceled',
    )

    list_filter = (
        'status',
        'start',
        'end',
    )

    inlines = [
            TicketTypeInline
    ]
