# Generated by Django 3.2.3 on 2024-04-22 05:27

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('recipes', '0005_auto_20240421_2100'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='shoppingcart',
            name='recipe',
        ),
        migrations.RemoveField(
            model_name='shoppingcart',
            name='user',
        ),
        migrations.AlterModelOptions(
            name='recipe',
            options={'default_related_name': 'recipes', 'ordering': ('created',), 'verbose_name': 'рецепт', 'verbose_name_plural': 'Рецепты'},
        ),
        migrations.AddField(
            model_name='recipe',
            name='favorite',
            field=models.ManyToManyField(related_name='favorite_recipes', to=settings.AUTH_USER_MODEL, verbose_name='Избранное'),
        ),
        migrations.AddField(
            model_name='recipe',
            name='shopping_cart',
            field=models.ManyToManyField(related_name='shopping_cart_recipes', to=settings.AUTH_USER_MODEL, verbose_name='Список покупок'),
        ),
        migrations.DeleteModel(
            name='Favorite',
        ),
        migrations.DeleteModel(
            name='ShoppingCart',
        ),
    ]
