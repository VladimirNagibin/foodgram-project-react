# Generated by Django 3.2.3 on 2024-05-06 11:20

from django.conf import settings
import django.contrib.auth.models
import django.contrib.auth.password_validation
import django.contrib.auth.validators
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.expressions
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('recipes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('password', models.CharField(max_length=150, validators=[django.contrib.auth.password_validation.validate_password], verbose_name='Пароль')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='Почта')),
                ('first_name', models.CharField(max_length=150, verbose_name='Имя')),
                ('last_name', models.CharField(max_length=150, verbose_name='Фамилия')),
                ('favorites', models.ManyToManyField(blank=True, related_name='favorite_users', to='recipes.Recipe', verbose_name='Избранное')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
                ('shopping_cart', models.ManyToManyField(blank=True, related_name='shopping_cart_users', to='recipes.Recipe', verbose_name='Список покупок')),
            ],
            options={
                'verbose_name': 'пользователь',
                'verbose_name_plural': 'Пользователи',
                'ordering': ('username',),
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='SubscriptionUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscribers', to=settings.AUTH_USER_MODEL, verbose_name='Автор')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='authors', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'подписка',
                'verbose_name_plural': 'Подписки',
            },
        ),
        migrations.AddField(
            model_name='user',
            name='subscriptions',
            field=models.ManyToManyField(related_name='followers', through='users.SubscriptionUser', to=settings.AUTH_USER_MODEL, verbose_name='Подписки'),
        ),
        migrations.AddField(
            model_name='user',
            name='user_permissions',
            field=models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions'),
        ),
        migrations.AddConstraint(
            model_name='subscriptionuser',
            constraint=models.UniqueConstraint(fields=('user', 'author'), name='unique_user_following'),
        ),
        migrations.AddConstraint(
            model_name='subscriptionuser',
            constraint=models.CheckConstraint(check=models.Q(('author', django.db.models.expressions.F('user')), _negated=True), name='prevent_self_follow'),
        ),
    ]
