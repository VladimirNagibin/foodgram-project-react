from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.utils.safestring import mark_safe

from .constants import MAX_HEIGHT_IMAGE_SIZE
from .servises import object_link

User = get_user_model()

admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Персональная информация', {'fields': ('first_name',
                                                'last_name',
                                                'email')}),
        ('Статусы', {'fields': ('is_active',
                                'is_staff',
                                'is_superuser')}),
        ('Рецепты пользователя', {'fields': ('recipes_of_user', )}),
        ('Избранные рецепты', {'fields': ('favorite', )}),
        ('Рецепты в корзине', {'fields': ('shopping_cart', )}),
        ('Подписан на авторов', {'fields': ('subscription', )}),
        ('Даты', {'fields': ('last_login',
                             'date_joined')}),

    )

    list_display = (
        'username',
        'first_name',
        'last_name',
        'email',
        'recipes_count',
        'is_staff',
    )
    list_filter = ('email', 'username')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    list_editable = ('first_name', 'last_name', 'email')
    filter_horizontal = ('favorite', 'shopping_cart', 'subscription')
    readonly_fields = ('recipes_of_user',)

    @admin.display(description='Кол-во рецептов у пользователя')
    def recipes_count(self, obj):
        return obj.recipes.count()

    @admin.display(description='Рецепты пользователя')
    def recipes_of_user(self, obj):
        recipes = ", ".join(
            [(f'<img src={recipe.image.url} '
              f'style="max-height: {MAX_HEIGHT_IMAGE_SIZE}px;"> '
              f'{object_link(recipe)}') for recipe in obj.recipes.all()]
        )
        return mark_safe(recipes)
