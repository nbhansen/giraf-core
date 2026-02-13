from django.contrib import admin

from apps.grades.models import Grade


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ["name", "organization"]
    list_filter = ["organization"]
    search_fields = ["name"]
