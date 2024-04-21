from django.contrib.auth import get_user_model
from django.db import models

from recipes.constants import NAME_MAX_LENGHT, TEXT_LIMIT

User = get_user_model()


class NameModel(models.Model):
    name = models.CharField('Название', max_length=NAME_MAX_LENGHT)

    class Meta:
        abstract = True
        ordering = ('name',)

    def __str__(self):
        return self.name[:TEXT_LIMIT]


class UserModel(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )

    class Meta:
        abstract = True
