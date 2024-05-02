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

    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('is_subscribed',)

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return (
            obj in user.subscription.all() if user and user.is_authenticated
            else False
        )


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


class SubscriptionRecipeSerialiser(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с Subscription."""

    is_subscribed = serializers.BooleanField()
    recipes_count = serializers.IntegerField(read_only=True, default=0)
    recipes = serializers.SerializerMethodField()

    def get_recipes(self, obj):
        recipes_limit = self.context.get('request').query_params.get(
            'recipes_limit'
        )
        recipes_limit = (obj.recipes_count if not recipes_limit
                         else int(recipes_limit))
        return SubscriptionRecipeSerialiser(
            obj._prefetched_objects_cache['recipes'][:recipes_limit], many=True
        ).data

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )


class UserSubscribeSerializer(serializers.Serializer):

    def validate(self, data):
        author = self.context.get('author')
        request = self.context.get('request')
        user = self.instance
        if user == author:
            raise serializers.ValidationError(
                'Невозможно подписаться/отписаться на себя.'
            )
        if author in user.subscription.all() and request.method == 'POST':
            raise serializers.ValidationError(
                'Подписка уже оформлена.'
            )
        elif (
            author not in user.subscription.all()
                and request.method == 'DELETE'
        ):
            raise serializers.ValidationError(
                'Подписка ещё не оформлена.'
            )
        data['author'] = author
        return data

    def update(self, instance, validated_data):
        instance.subscription.add(validated_data['author'])
        return instance


class IngredientRecipeSerialiser(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient_id')
    name = serializers.SerializerMethodField()
    measurement_unit = serializers.SerializerMethodField()
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def get_name(self, obj):
        return obj.ingredient.name

    def get_measurement_unit(self, obj):
        return obj.ingredient.measurement_unit


class TagRelatedField(serializers.PrimaryKeyRelatedField):

    def to_representation(self, value):
        return TagSerialiser(value).data


class RecipeSerialiser(serializers.ModelSerializer):

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
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(min_value=1)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )
        read_only_fields = (
            'id',
            'author',
            'is_favorited',
            'is_in_shopping_cart'
        )

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        return (
            obj in user.favorite.all() if user and user.is_authenticated
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


class UserFavoriteSerializer(serializers.Serializer):

    def validate(self, data):
        request = self.context.get('request')
        recipe_id = request.parser_context.get('kwargs')['recipe_id']
        if not Recipe.objects.filter(id=recipe_id):
            if request.method == 'POST':
                raise serializers.ValidationError(
                    'Рецепт не найден.',
                )
            else:
                raise Http404('Рецепт не найден.')
        if self.instance.favorite.filter(id=recipe_id):
            if request.method == 'POST':
                raise serializers.ValidationError(
                    'В избранное уже был добавлен рецепт.'
                )
        else:
            if request.method == 'DELETE':
                raise serializers.ValidationError(
                    'В избранное ещё не был добавлен рецепт для удаления.'
                )
        data['recipe_id'] = recipe_id
        return data

    def update(self, instance, validated_data):
        instance.favorite.add(validated_data['recipe_id'])
        return instance


class UserShoppingCartSerializer(serializers.Serializer):

    def validate(self, data):
        request = self.context.get('request')
        recipe_id = request.parser_context.get('kwargs')['recipe_id']
        if not Recipe.objects.filter(id=recipe_id):
            if request.method == 'POST':
                raise serializers.ValidationError(
                    'Рецепт не найден.',
                )
            else:
                raise Http404('Рецепт не найден.')
        if self.instance.shopping_cart.filter(id=recipe_id):
            if request.method == 'POST':
                raise serializers.ValidationError(
                    'В список покупок уже был добавлен рецепт.'
                )
        else:
            if request.method == 'DELETE':
                raise serializers.ValidationError(
                    'В список покупок ещё не был добавлен рецепт для удаления.'
                )
        data['recipe_id'] = recipe_id
        return data

    def update(self, instance, validated_data):
        instance.shopping_cart.add(validated_data['recipe_id'])
        return instance
