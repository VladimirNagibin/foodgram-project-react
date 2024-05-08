# Generated by Django 3.2.3 on 2024-05-08 05:25

import colorfield.fields
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Ingredient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Название')),
                ('measurement_unit', models.CharField(choices=[('банка', 'банка'), ('батон', 'батон'), ('бутылка', 'бутылка'), ('веточка', 'веточка'), ('г', 'г'), ('горсть', 'горсть'), ('долька', 'долька'), ('звездочка', 'звездочка'), ('зубчик', 'зубчик'), ('капля', 'капля'), ('кг', 'кг'), ('кусок', 'кусок'), ('л', 'л'), ('лист', 'лист'), ('мл', 'мл'), ('пакет', 'пакет'), ('пакетик', 'пакетик'), ('пачка', 'пачка'), ('пласт', 'пласт'), ('по вкусу', 'по вкусу'), ('пучок', 'пучок'), ('ст. л.', 'ст. л.'), ('стакан', 'стакан'), ('стебель', 'стебель'), ('стручок', 'стручок'), ('тушка', 'тушка'), ('упаковка', 'упаковка'), ('ч. л.', 'ч. л.'), ('шт.', 'шт.'), ('щепотка', 'щепотка')], max_length=9, verbose_name='Единица измерения')),
            ],
            options={
                'verbose_name': 'ингредиент',
                'verbose_name_plural': 'Ингредиенты',
                'ordering': ('name',),
                'abstract': False,
                'default_related_name': 'ingredients',
            },
        ),
        migrations.CreateModel(
            name='IngredientRecipe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.PositiveSmallIntegerField(verbose_name='Количество')),
            ],
            options={
                'verbose_name': 'ингредиент',
                'verbose_name_plural': 'Ингредиенты',
                'ordering': ('ingredient',),
                'default_related_name': 'ingredient_recipes',
            },
        ),
        migrations.CreateModel(
            name='Recipe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Название')),
                ('image', models.ImageField(upload_to='recipes/', verbose_name='Картинка')),
                ('text', models.TextField(verbose_name='Описание')),
                ('cooking_time', models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1, message='Задайте время приготовления')], verbose_name='Время приготовления')),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Дата добавления')),
            ],
            options={
                'verbose_name': 'рецепт',
                'verbose_name_plural': 'Рецепты',
                'ordering': ('created',),
                'abstract': False,
                'default_related_name': 'recipes',
            },
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True, verbose_name='Название')),
                ('color', colorfield.fields.ColorField(default='#FFFFFF', image_field=None, max_length=25, samples=None, unique=True, verbose_name='Цвет')),
                ('slug', models.SlugField(max_length=200, unique=True, verbose_name='Слаг')),
            ],
            options={
                'verbose_name': 'тег',
                'verbose_name_plural': 'Теги',
                'ordering': ('name',),
            },
        ),
    ]
