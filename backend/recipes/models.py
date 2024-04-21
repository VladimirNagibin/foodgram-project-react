from django.contrib.auth import get_user_model
from django.db import models

from core.models import NameModel, UserModel
from .constants import (
    MEASU_MAX_LENGHT,
    MEASU_CHOICES,
    SLUG_MAX_LENGHT,
    COLOR_MAX_LENGHT
)
from .validators import validate_color

User = get_user_model()


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
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )
    image = models.ImageField(
        upload_to='recipes/', null=True, blank=True
    )
    text = models.TextField('Описание')
    coocking_time = models.PositiveSmallIntegerField('Время приготовления')
    ingredient = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиент',
        through='IngredientRecipe'
    )
    tag = models.ManyToManyField(Tag, verbose_name='Тэг')
    created = models.DateTimeField(
        'Дата добавления', auto_now_add=True, db_index=True
    )

    class Meta(UserModel.Meta):
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'
        default_related_name = 'recipes'


class IngredientRecipe(models.Model):
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    amount = models.PositiveSmallIntegerField('Количество')

    def __str__(self):
        return f'{self.ingredient} {self.recipe}'


class Favorite(UserModel):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta(UserModel.Meta):
        verbose_name = 'избранное'
        verbose_name_plural = 'Избранные'
        default_related_name = 'favorites'

    def __str__(self):
        return f'{self.user}: {self.recipe}'


class ShoppingCart(UserModel):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta(UserModel.Meta):
        verbose_name = 'список покупок'
        verbose_name_plural = 'Списки покупок'
        default_related_name = 'shopping_cart'

    def __str__(self):
        return f'{self.user}: {self.recipe}'


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='authors',
        verbose_name='Пользователь',
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followers',
        verbose_name='Подписки',
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'following'),
                name='unique_user_following'
            ),
            models.CheckConstraint(
                name='prevent_self_follow',
                check=~models.Q(user=models.F('following')),
            ),
        )
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'
