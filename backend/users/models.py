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
    favorites = models.ManyToManyField(
        'recipes.Recipe',
        verbose_name='Избранное',
        related_name='favorite_users',
        blank=True,
    )
    shopping_cart = models.ManyToManyField(
        'recipes.Recipe',
        verbose_name='Список покупок',
        related_name='shopping_cart_users',
        blank=True,
    )
    subscriptions = models.ManyToManyField(
        'User',
        through='SubscriptionUser',
        symmetrical=False,
        verbose_name='Подписки',
        related_name='followers'
    )

    class Meta:
        ordering = ('username',)
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class SubscriptionUser(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='authors'
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        related_name='subscribers',
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_user_following'
            ),
            models.CheckConstraint(
                name='prevent_self_follow',
                check=~models.Q(author=models.F('user')),
            ),
        )

    def __str__(self):
        return f'{self.author}'
