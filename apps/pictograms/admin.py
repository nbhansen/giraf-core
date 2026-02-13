from django.contrib import admin

from apps.pictograms.models import Pictogram


@admin.register(Pictogram)
class PictogramAdmin(admin.ModelAdmin):
    list_display = ["name", "organization", "image_url"]
    list_filter = ["organization"]
    search_fields = ["name"]
