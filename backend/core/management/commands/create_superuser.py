import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from dotenv import load_dotenv

load_dotenv()

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates a superuser from environment variables.'

    def handle(self, *args, **kwargs):
        if kwargs['update']:
            User.objects.filter(is_superuser=True).delete()
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                username=os.getenv('SUPERUSER_USERNAME'),
                email=os.getenv('SUPERUSER_EMAIL'),
                password=os.getenv('SUPERUSER_PASSWORD')
            )
            self.stdout.write(self.style.SUCCESS(
                'Successfully created a new superuser'
            ))
        else:
            self.stdout.write(self.style.WARNING('A superuser already exists'))

    def add_arguments(self, parser):
        parser.add_argument(
            '-u',
            '--update',
            action='store_true',
            default=False,
            help='Удалить текущего суперпользователя если существует.'
        )
