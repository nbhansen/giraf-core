from django.contrib import admin

from apps.organizations.models import Membership, Organization


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 0


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ["name", "created_at"]
    search_fields = ["name"]
    inlines = [MembershipInline]


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ["user", "organization", "role", "joined_at"]
    list_filter = ["role"]
    search_fields = ["user__username", "organization__name"]
