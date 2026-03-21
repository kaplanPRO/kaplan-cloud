from django.contrib import admin

from .models import UserRegistrationToken


class TokenStatusFilter(admin.SimpleListFilter):
    title = "status"
    parameter_name = "status"

    def lookups(self, request, model_admin):
        return [
            ("available", "Available"),
            ("used", "Used"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "available":
            return queryset.filter(user__isnull=True)
        if self.value() == "used":
            return queryset.filter(user__isnull=False)


@admin.register(UserRegistrationToken)
class UserRegistrationTokenAdmin(admin.ModelAdmin):
    list_display = ("token", "user_type", "user", "created_at")
    list_filter = (TokenStatusFilter,)
    readonly_fields = ("user", "created_at")
