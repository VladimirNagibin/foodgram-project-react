from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.utils.safestring import mark_safe

from recipes.models import FavoriteUser, ShoppingCartUser
from users.constants import MAX_HEIGHT_IMAGE_SIZE
from users.models import SubscriptionUser, User
from users.servises import object_link

admin.site.unregister(Group)


class UserSubscriptorInline(admin.TabularInline):
    model = SubscriptionUser
    extra = 1
    fk_name = 'user'


class UserFavoriteInline(admin.TabularInline):
    model = FavoriteUser
    extra = 1


class UserFShoppingCartInline(admin.TabularInline):
    model = ShoppingCartUser
    extra = 1


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
        ('Даты', {'fields': ('last_login',
                             'date_joined')}),

    )

    list_display = (
        'username',
        'first_name',
        'last_name',
        'email',
        'recipes_count',
        'subscribers_count',
        'is_staff',
    )
    list_filter = ('email', 'username')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    list_editable = ('first_name', 'last_name', 'email')
    readonly_fields = ('recipes_of_user',)
    inlines = (UserSubscriptorInline, UserFavoriteInline,
               UserFShoppingCartInline)

    @admin.display(description='Кол-во рецептов.')
    def recipes_count(self, obj):
        return obj.recipes.count()

    @admin.display(description='Рецепты пользователя.')
    def recipes_of_user(self, obj):
        recipes = ', '.join(
            [(f'<img src={recipe.image.url} '
              f'style="max-height: {MAX_HEIGHT_IMAGE_SIZE}px;"> '
              f'{object_link(recipe)}') for recipe in obj.recipes.all()]
        )
        return mark_safe(recipes)

    @admin.display(description='Кол-во подписчиков.')
    def subscribers_count(self, obj):
        return obj.subscribers.count()
