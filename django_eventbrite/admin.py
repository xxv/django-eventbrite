from django.contrib import admin

from .models import Event

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    readonly_fields = ('eb_id','eb_url',)
