from django.contrib.auth import get_user_model
# from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from recipes.models import Ingredient, Subscription, Tag
from users.constants import PASSWORD_MAX_LENGHT

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с моделью User."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        return Subscription.objects.filter(
            user=self.context.get('request').user, following=obj
        ).exists()


class UserSetPasswordSerialiser(serializers.Serializer):
    current_password = serializers.CharField(max_length=PASSWORD_MAX_LENGHT)
    new_password = serializers.CharField(max_length=PASSWORD_MAX_LENGHT)

    # def validate_new_password(self, value):
    #    validate_password(value)
    #    return value

    def validate_current_password(self, value):
        if not self.context.get('request').user.check_password(value):
            raise serializers.ValidationError(
                ('Ваш текущий пароль не корректный. Введите пароль снова.')
            )
        return value

    def update(self, instance, validated_data):
        instance.set_password(validated_data['new_password'])
        instance.save()
        return instance


class TagSerialiser(serializers.ModelSerializer):
    """Сериализатор для работы с моделью Tag."""

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerialiser(serializers.ModelSerializer):
    """Сериализатор для работы с моделью Ingredient."""

    class Meta:
        model = Ingredient
        fields = '__all__'