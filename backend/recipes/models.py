from django.contrib.auth import get_user_model
from django.db import models

from core.models import NameModel
from .constants import (
    MEASU_MAX_LENGHT,
    MEASU_CHOICES,
    SLUG_MAX_LENGHT,
    COLOR_MAX_LENGHT
)
from .validators import validate_color

# User = get_user_model()


class Ingredient(NameModel):
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=MEASU_MAX_LENGHT,
        choices=MEASU_CHOICES,
    )

    class Meta(NameModel.Meta):
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'
        default_related_name = 'ingredients'

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Tag(NameModel):
    color = models.CharField(
        'Цвет',
        max_length=COLOR_MAX_LENGHT,
        blank=True,
        null=True,
        validators=(validate_color, )
    )
    slug = models.SlugField(
        'Слаг',
        max_length=SLUG_MAX_LENGHT,
        blank=True,
        null=True,
        unique=True,
    )

    class Meta(NameModel.Meta):
        verbose_name = 'тэг'
        verbose_name_plural = 'Тэги'


class Recipe(NameModel):
    author = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )
    image = models.ImageField(
        upload_to='recipes/'
    )
    text = models.TextField('Описание')
    cooking_time = models.PositiveSmallIntegerField('Время приготовления')
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиент',
        through='IngredientRecipe'
    )
    tags = models.ManyToManyField(Tag, verbose_name='Тэг')
    created = models.DateTimeField(
        'Дата добавления', auto_now_add=True, db_index=True
    )

    class Meta(NameModel.Meta):
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'
        default_related_name = 'recipes'
        ordering = ('created',)


class IngredientRecipe(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_recipes',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredient_recipes',
    )
    amount = models.PositiveSmallIntegerField('Количество')

    def __str__(self):
        return f'{self.ingredient} {self.recipe}'
