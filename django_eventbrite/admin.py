from django.contrib import admin

from . import models

class EventAdmin(admin.ModelAdmin):
    readonly_fields = ('eb_id','eb_url',)

admin.site.register(models.Event, EventAdmin)
