from django.contrib import admin

from .models import Event, TicketType

class TicketTypeInline(admin.StackedInline):
    model = TicketType

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    search_fields = ['name', 'description']
    readonly_fields = ('eb_id','eb_url',)
    inlines = [
            TicketTypeInline
            ]

@admin.register(TicketType)
class TicketTypeAdmin(admin.ModelAdmin):
    search_fields = ['name', 'description']
    readonly_fields = ('eb_id',)
