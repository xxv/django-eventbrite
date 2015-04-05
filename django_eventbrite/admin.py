from django.contrib import admin

from .models import Event, TicketType

class TicketTypeInline(admin.StackedInline):
    model = TicketType
    readonly_fields = ('eb_id',)

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    search_fields = ['name', 'description']
    readonly_fields = ('eb_id','eb_url',)
    list_display = ('name', 'start', 'end', 'status', 'capacity', 'quantity_sold')
    list_filter = (
        ('status',)
            )
    inlines = [
            TicketTypeInline
            ]
