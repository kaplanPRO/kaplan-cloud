from datetime import timedelta

from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import UserRegistrationToken

TOKEN_EXPIRY_HOURS = 48


class UserRegistrationForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(
        label="Password confirmation",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        strip=False,
        help_text="Enter the same password as before, for verification.",
    )
    token = forms.CharField(
        max_length=64, help_text="Enter your registration token here."
    )

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email")

        field_order = [
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
            "token",
        ]

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError(
                "The two password fields did not match.",
                code="password_mismatch",
            )
        return password2

    def clean_token(self):
        token_value = self.cleaned_data.get("token")
        try:
            token = UserRegistrationToken.objects.get(token=token_value)
        except UserRegistrationToken.DoesNotExist:
            raise ValidationError("Invalid registration token.")

        if token.user is not None:
            raise ValidationError("This registration token has already been used.")

        expiry_threshold = timezone.now() - timedelta(hours=TOKEN_EXPIRY_HOURS)
        if token.created_at < expiry_threshold:
            raise ValidationError("This registration token has expired.")

        return token

    def _post_clean(self):
        super()._post_clean()
        password = self.cleaned_data["password2"]
        try:
            password_validation.validate_password(password, self.instance)
        except forms.ValidationError as error:
            self.add_error("password2", error)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            token = self.cleaned_data["token"]
            if token.user_type == 1:
                user.groups.add(Group.objects.get(name="PM"))
                user.is_staff = True
                user.save()
            token.user = user
            token.save()

        return user
