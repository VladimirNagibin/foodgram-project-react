from django.contrib import admin
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
    extra = 0


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    fields = (
        'name',
        'author',
        'image',
        'image_of_recipe',
        'favorite_users_count',
        'cooking_time',
        'tags',
        'text',
    )
    list_display = (
        'name', 'author', 'image_of_recipe', 'favorite_users_count'
    )
    search_fields = ('name', 'author', 'tags')
    list_filter = ('tags', 'author', 'name')
    readonly_fields = ('image_of_recipe', 'favorite_users_count')
    filter_horizontal = ('tags',)
    inlines = (IngredientRecipeInline,)

    @admin.display(description='Отображение картинки')
    def image_of_recipe(self, obj):
        if obj.image:
            return mark_safe(
                f'<img src={obj.image.url} '
                f'width="{IMAGE_SIZE}" height="{IMAGE_SIZE}">'
            )

    @admin.display(description='Кол-во добавлений в избранное')
    def favorite_users_count(self, obj):
        return obj.favorite_users.count()
