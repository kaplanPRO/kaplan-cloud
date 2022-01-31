from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import password_validation

from .models import UserRegistrationToken

class UserRegistrationForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Password',
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(
        label='Password confirmation',
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        strip=False,
        help_text='Enter the same password as before, for verification.',
    )
    token = forms.CharField(
        max_length=8,
        help_text='Enter your registration token here.'
    )

    class Meta:
        model = User
        fields = ('username','first_name','last_name','email')

    field_order = ['username', 'first_name', 'last_name', 'email',
                   'password1','password2','token']

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError(
                'The two password fields did not match.',
                code='password_mismatch',
            )
        return password2

    def clean_token(self):
        try:
            token = UserRegistrationToken.objects.get(token=self.cleaned_data.get('token'))
        except UserRegistrationToken.DoesNotExist as error:
            self.add_error('token', error)

        return token

    def _post_clean(self):
        super()._post_clean()
        password = self.cleaned_data['password2']
        try:
            password_validation.validate_password(password, self.instance)
        except ValidationError as error:
            self.add_error('password2', error)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            token = self.cleaned_data['token']
            if token.user_type == 1:
                user.groups.add(1)
            token.user = user
            token.save()

        return user
