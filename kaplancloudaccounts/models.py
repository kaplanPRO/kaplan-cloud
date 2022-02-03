from django.contrib.auth.models import User
from django.db import models

from .utils import generate_random_token

# Create your models here.

user_types = (
    (0, 'Translator'),
    (1, 'PM')
)

class UserRegistrationToken(models.Model):
    token = models.CharField(max_length=8, unique=True, default=generate_random_token)
    user_type = models.IntegerField(choices=user_types, default=0)
    user = models.ForeignKey(User, models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return self.token
