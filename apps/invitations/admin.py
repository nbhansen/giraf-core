from django.contrib import admin

from apps.invitations.models import Invitation


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ["receiver", "organization", "sender", "status", "created_at"]
    list_filter = ["status", "organization"]
    search_fields = ["receiver__username", "sender__username", "organization__name"]
    readonly_fields = ["created_at"]
