from django.contrib import admin

from apps.citizens.models import Citizen


@admin.register(Citizen)
class CitizenAdmin(admin.ModelAdmin):
    list_display = ["first_name", "last_name", "organization"]
    list_filter = ["organization"]
    search_fields = ["first_name", "last_name"]
