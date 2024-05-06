from django.db import models

from recipes.constants import NAME_MAX_LENGHT, TEXT_LIMIT


class NameModel(models.Model):
    name = models.CharField(
        'Название',
        max_length=NAME_MAX_LENGHT,
    )

    class Meta:
        abstract = True
        ordering = ('name',)

    def __str__(self):
        return self.name[:TEXT_LIMIT]
