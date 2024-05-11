from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .constants import IMAGE_SIZE
from .models import Ingredient, IngredientRecipe, Recipe, Tag


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')
    search_fields = ('name', 'color', 'slug')
    list_filter = ('name', 'color', 'slug')
    list_editable = ('color', 'slug')


class IngredientRecipeInline(admin.TabularInline):
    model = IngredientRecipe
    min_num = 1
    extra = 0


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    fields = (
        'name',
        'author_',
        'image',
        'image_of_recipe',
        'favorite_users_count',
        'cooking_time',
        'tags',
        'text',
        'tags_',
        'ingredients_'
    )
    list_display = ('name', 'author_', 'tags_', 'ingredients_',
                    'image_of_recipe', 'favorite_users_count')
    search_fields = ('name', 'tags')
    list_filter = ('tags', 'author', 'name')
    readonly_fields = ('image_of_recipe', 'favorite_users_count', 'author_',
                       'tags_', 'ingredients_')
    filter_horizontal = ('tags',)
    inlines = (IngredientRecipeInline,)

    @admin.display(description='Отображение картинки')
    def image_of_recipe(self, obj):
        return mark_safe(
            f'<img src={obj.image.url} '
            f'width="{IMAGE_SIZE}" height="{IMAGE_SIZE}">'
        )

    @admin.display(description='Кол-во добавлений в избранное')
    def favorite_users_count(self, obj):
        return obj.favorite_users.count()

    @admin.display(description='Автор')
    def author_(self, obj):
        link = reverse(
            'admin:users_user_change', args=[obj.author.id]
        )
        return format_html('<a href="{}">{}</a>', link, obj.author)

    @admin.display(description='Тэги')
    def tags_(self, obj):
        return ', '.join([tag.name for tag in obj.tags.all()])

    @admin.display(description='Ингредиенты')
    def ingredients_(self, obj):
        return ', '.join(
            [ingredient.name for ingredient in obj.ingredients.all()]
        )
