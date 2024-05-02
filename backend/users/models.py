from django.contrib.auth.models import AbstractUser
from django.contrib.auth.password_validation import validate_password
from django.db import models

from users.constants import (EMAIL_MAX_LENGHT, NAME_MAX_LENGHT,
                             PASSWORD_MAX_LENGHT)


class User(AbstractUser):
    password = models.CharField(
        max_length=PASSWORD_MAX_LENGHT,
        verbose_name='Пароль',
        validators=(validate_password, )
    )
    email = models.EmailField(
        max_length=EMAIL_MAX_LENGHT,
        unique=True,
        verbose_name='Почта'
    )
    first_name = models.CharField(
        max_length=NAME_MAX_LENGHT,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=NAME_MAX_LENGHT,
        verbose_name='Фамилия'
    )
    favorite = models.ManyToManyField(
        'recipes.Recipe',
        verbose_name='Избранное',
        related_name='favorite_users'
    )
    shopping_cart = models.ManyToManyField(
        'recipes.Recipe',
        verbose_name='Список покупок',
        related_name='shopping_cart_users'
    )
    subscription = models.ManyToManyField(
        'User',
        verbose_name='Подписки',
        related_name='followers'
    )

    class Meta:
        ordering = ('username',)
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'{self.first_name} {self.last_name}'
