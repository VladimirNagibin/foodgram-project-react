import csv

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import IntegrityError

from recipes.models import Ingredient, Tag

DIR_DATA = '../data'
DATA = (
    ('ingredients.csv',
     Ingredient,
     ['name', 'measurement_unit']),
    ('tag.csv',
     Tag,
     ['name', 'color', 'slug']),
)


class Command(BaseCommand):

    def load_obj(self, filename, obj, fields):
        try:
            with open(f'{DIR_DATA}/{filename}', encoding='utf-8') as file_data:
                reader = csv.reader(file_data)
                for row in reader:
                    object_value = {
                        key: value for key, value in zip(fields, row)
                    }
                    try:
                        obj.objects.update_or_create(**object_value)
                    except IntegrityError:
                        self.stdout.write(f'Файл {filename} не корректные '
                                          f'данные: {object_value} для '
                                          f'{obj.__name__}')

        except FileNotFoundError:
            self.stdout.write(f'Файл {filename} невозможно открыть')
        except Exception as e:
            self.stdout.write(f'Ошибка {e} при работе с файлом {filename}')
        self.stdout.write(f'Файл {filename} загружен')

    def handle(self, *args, **kwargs):
        for filename, obj, fields in DATA:
            if kwargs['erase']:
                obj.objects.all().delete()
            self.load_obj(filename, obj, fields)

    def add_arguments(self, parser):
        parser.add_argument(
            '-e',
            '--erase',
            action='store_true',
            default=False,
            help='Очистить таблицу перед загрузкой'
        )