from colorfield.fields import ColorField
from django.contrib.auth import get_user_model
from django.db import models

from core.models import NameModel
from .constants import (
    MEASU_MAX_LENGHT,
    MEASU_CHOICES,
    SLUG_MAX_LENGHT,
)

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
    color = ColorField('Цвет', unique=True, default='#FFFFFF')
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
        'Картинка',
        upload_to='recipes/'
    )
    text = models.TextField('Описание')
    cooking_time = models.PositiveSmallIntegerField('Время приготовления')
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиенты',
        through='IngredientRecipe'
    )
    tags = models.ManyToManyField(Tag, verbose_name='Тэги')
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
        verbose_name='Ингредиент',
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
    )
    amount = models.PositiveSmallIntegerField('Количество')

    class Meta(NameModel.Meta):
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'
        default_related_name = 'ingredient_recipes'
        ordering = ('ingredient',)

    def __str__(self):
        return f'{self.ingredient} {self.recipe}'
