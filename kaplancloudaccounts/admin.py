from django.contrib import admin

from .models import UserRegistrationToken


@admin.register(UserRegistrationToken)
class UserRegistrationTokenAdmin(admin.ModelAdmin):
    list_display = ("token", "user_type", "user", "created_at")
    readonly_fields = ("created_at",)
