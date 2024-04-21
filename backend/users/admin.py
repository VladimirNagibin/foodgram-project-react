from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group

User = get_user_model()

admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'username',
        'first_name',
        'last_name',
        'email',
        'recipes_count',
        'is_staff',
    )
    list_filter = ('email', 'username')
    search_fields = ('email', 'username')
    list_editable = ('first_name', 'last_name')

    @admin.display(description='Кол-во рецептов у пользователя')
    def recipes_count(self, obj):
        return obj.recipes.count()
