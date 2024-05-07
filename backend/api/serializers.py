from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.http import Http404
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import Ingredient, IngredientRecipe, Recipe, Tag
from users.constants import PASSWORD_MAX_LENGHT

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )
        extra_kwargs = {
            'password': {'write_only': True},
            'id': {'read_only': True}
        }

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserIsSubscribedSerializer(UserSerializer):

    is_subscribed = serializers.BooleanField(read_only=True, default=False)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('is_subscribed',)


class UserWithRecipesSerializer(UserIsSubscribedSerializer):

    recipes_count = serializers.IntegerField(
        read_only=True,
        default=0
    )
    recipes = serializers.SerializerMethodField()

    class Meta(UserIsSubscribedSerializer.Meta):
        fields = (UserIsSubscribedSerializer.Meta.fields
                  + ('recipes', 'recipes_count',))

    def get_recipes(self, obj):
        recipes_limit = self.context.get('request').query_params.get(
            'recipes_limit'
        )
        recipes_limit = (obj.recipes_count if not recipes_limit
                         else int(recipes_limit))
        return RecipeMinifieldSerialiser(
            obj._prefetched_objects_cache['recipes'][:recipes_limit], many=True
        ).data


class UserSetPasswordSerialiser(serializers.Serializer):
    current_password = serializers.CharField(max_length=PASSWORD_MAX_LENGHT)
    new_password = serializers.CharField(max_length=PASSWORD_MAX_LENGHT)

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def validate_current_password(self, value):
        if not self.instance.check_password(value):
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


class IngredientRecipeSerialiser(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient_id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeMinifieldSerialiser(serializers.ModelSerializer):

    image = Base64ImageField()
    cooking_time = serializers.IntegerField(min_value=1)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id',)


class TagRelatedField(serializers.PrimaryKeyRelatedField):

    def to_representation(self, value):
        return TagSerialiser(value).data


class RecipeSerialiser(RecipeMinifieldSerialiser):

    is_favorited = serializers.SerializerMethodField(
        read_only=True,
        required=False
    )
    is_in_shopping_cart = serializers.SerializerMethodField(
        read_only=True,
        required=False
    )
    tags = TagRelatedField(many=True, queryset=Tag.objects.all())
    author = UserSerializer(read_only=True)
    ingredients = IngredientRecipeSerialiser(
        many=True,
        source='ingredient_recipes',
    )

    class Meta(RecipeMinifieldSerialiser.Meta):
        fields = (RecipeMinifieldSerialiser.Meta.fields
                  + ('tags', 'author', 'ingredients', 'is_favorited',
                     'is_in_shopping_cart', 'text'))
        read_only_fields = (RecipeMinifieldSerialiser.Meta.read_only_fields
                  + ('author', 'is_favorited', 'is_in_shopping_cart'))

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        return (
            obj in user.favorites.all() if user and user.is_authenticated
            else False
        )

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        return (
            obj in user.shopping_cart.all() if user and user.is_authenticated
            else False
        )

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Ингредиенты отсутствуют.'
            )
        if (
            len(set(
                [ingredient['ingredient_id'] for ingredient in value]
            )) < len(value)
        ):
            raise serializers.ValidationError(
                'Ингредиенты повторяются.'
            )
        for ingredient in value:
            if not Ingredient.objects.filter(id=ingredient['ingredient_id']):
                raise serializers.ValidationError(
                    'Ингредиент не найден.'
                )
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                'Тэги отсутствуют.'
            )
        if len(set(value)) < len(value):
            raise serializers.ValidationError(
                'Тэги повторяются.'
            )
        return value

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError(
                'Картинка отсутствуют.'
            )
        return value

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredient_recipes')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        for tag in tags:
            recipe.tags.add(tag)
        for ingredient_recipe in ingredients:
            recipe.ingredients.add(
                Ingredient.objects.get(id=ingredient_recipe['ingredient_id']),
                through_defaults={"amount": ingredient_recipe['amount']}
            )
        return recipe

    def update(self, instance, validated_data, **kwargs):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredient_recipes')
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        instance.tags.clear()
        for tag in tags:
            instance.tags.add(tag)
        instance.ingredients.clear()
        for ingredient_recipe in ingredients:
            instance.ingredients.add(
                Ingredient.objects.get(id=ingredient_recipe['ingredient_id']),
                through_defaults={"amount": ingredient_recipe['amount']}
            )
        return instance


class UserOptionSerializer(serializers.Serializer):
    object_for_option = Recipe

    def get_option_objects(self):
        ...

    def validate(self, data):
        request = self.context.get('request')
        id = request.parser_context.get('kwargs')['id']
        if not self.object_for_option.objects.filter(id=id):
            if request.method == 'POST' and self.object_for_option == Recipe:
                raise serializers.ValidationError(
                    'Объект не найден.',
                )
            else:
                raise Http404('Объект не найден.')
        if self.get_option_objects().filter(id=id):
            if request.method == 'POST':
                raise serializers.ValidationError(
                    'Не возможно добавить повторно.'
                )
        else:
            if request.method == 'DELETE':
                raise serializers.ValidationError(
                    'Объект для удаления ещё не добавлен.'
                )
        data['id'] = id
        return data

    def update(self, instance, validated_data):
        self.get_option_objects().add(validated_data['id'])
        return instance


class UserFavoriteSerializer(UserOptionSerializer):
    def get_option_objects(self):
        return self.instance.favorites


class UserShoppingCartSerializer(UserOptionSerializer):
    def get_option_objects(self):
        return self.instance.shopping_cart


class UserSubscribeSerializer(UserOptionSerializer):
    object_for_option = User

    def get_option_objects(self):
        return self.instance.subscriptions

    def validate(self, data):
        data = super().validate(data)
        if self.instance.id == int(data['id']):
            raise serializers.ValidationError(
                'Невозможно подписаться/отписаться на себя.'
            )
        return data
