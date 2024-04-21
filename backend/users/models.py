from django.contrib.auth.models import AbstractUser
from django.db import models

from .constants import PASSWORD_MAX_LENGHT, EMAIL_MAX_LENGHT


class User(AbstractUser):
    password = models.CharField(
        max_length=PASSWORD_MAX_LENGHT,
        verbose_name='Пароль'
    )
    email = models.EmailField(
        max_length=EMAIL_MAX_LENGHT,
        unique=True,
        verbose_name='Почта'
    )

    class Meta:
        ordering = ('username',)
