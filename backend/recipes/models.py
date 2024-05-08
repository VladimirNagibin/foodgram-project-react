from colorfield.fields import ColorField
from django.core.validators import MinValueValidator
from django.db import models

from core.models import NameModel
from recipes.constants import (AMOUNT_MIN_VALUE, COOKING_MIN_TIME,
                               MEASU_CHOICES, MEASU_MAX_LENGHT,
                               NAME_MAX_LENGHT, SLUG_MAX_LENGHT, TEXT_LIMIT)


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


class Tag(models.Model):
    name = models.CharField(
        'Название',
        max_length=NAME_MAX_LENGHT,
        unique=True,
    )
    color = ColorField('Цвет', unique=True)
    slug = models.SlugField(
        'Слаг',
        max_length=SLUG_MAX_LENGHT,
        unique=True,
    )

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name[:TEXT_LIMIT]


class Recipe(NameModel):
    author = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )
    image = models.ImageField(
        'Картинка',
        upload_to='recipes/',
    )
    text = models.TextField('Описание')
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления',
        validators=(
            MinValueValidator(COOKING_MIN_TIME,
                              message='Задайте время приготовления'),
        ),
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиенты',
        through='IngredientRecipe',
    )
    tags = models.ManyToManyField(Tag, verbose_name='Теги')
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
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=(
            MinValueValidator(AMOUNT_MIN_VALUE,
                              message='Задайте количество ингредиента.'),
        ),
    )

    class Meta:
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'
        default_related_name = 'ingredient_recipes'
        ordering = ('ingredient',)
        constraints = (
            models.UniqueConstraint(
                fields=('ingredient', 'recipe'),
                name='unique_ingredient_recipe'
            ),
        )

    def __str__(self):
        return f'{self.ingredient} {self.recipe}'
