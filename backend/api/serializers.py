# from pprint import pprint

from django.db.models import Count
# from django.http import Http404
from django.shortcuts import get_object_or_404
from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (FavoriteUser, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCartUser, Tag)
from users.models import SubscriptionUser, User


class UserSerializer(DjoserUserSerializer):

    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta(DjoserUserSerializer):
        model = User
        fields = DjoserUserSerializer.Meta.fields + ('is_subscribed',)

    def get_is_subscribed(self, obj):
        request = self.context['request']
        return bool(request and request.user.is_authenticated
                    and SubscriptionUser.objects.filter(user=request.user,
                                                        author=obj))


class UserWithRecipesSerializer(UserSerializer):

    recipes_count = serializers.IntegerField(
        read_only=True,
        default=0
    )
    recipes = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = (UserSerializer.Meta.fields
                  + ('recipes', 'recipes_count',))

    def get_recipes(self, obj):
        recipes_user = Recipe.objects.filter(author=obj)

        recipes_limit = self.context['request'].query_params.get(
            'recipes_limit'
        )
        if recipes_limit:
            recipes_user = recipes_user[:int(recipes_limit)]
        return RecipeMinifieldSerialiser(recipes_user, many=True).data


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

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class TagRelatedField(serializers.PrimaryKeyRelatedField):

    def to_representation(self, value):
        return TagSerialiser(value).data


class RecipeSerialiser(RecipeMinifieldSerialiser):

    image = Base64ImageField()
    cooking_time = serializers.IntegerField(min_value=1)
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
        read_only_fields = (
            'id', 'author', 'is_favorited', 'is_in_shopping_cart'
        )

    def get_is_favorited(self, obj):
        request = self.context['request']
        return bool(request and request.user.is_authenticated
                    and FavoriteUser.objects.filter(user=request.user,
                                                    recipe=obj))

    def get_is_in_shopping_cart(self, obj):
        request = self.context['request']
        return bool(request and request.user.is_authenticated
                    and ShoppingCartUser.objects.filter(user=request.user,
                                                        recipe=obj))

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                [{'ingredient': ['Ингредиенты отсутствуют.']}]
            )
        error = []
        ingredients_id = set()
        for ingredient in value:
            id = ingredient['ingredient_id']
            if not Ingredient.objects.filter(id=id):
                error.append(
                    {'ingredient': [f'Ингредиент с id:{id} не найден.']}
                )
            else:
                ingredient_name = Ingredient.objects.get(id=id).name
                if id in ingredients_id:
                    error.append(
                        {'ingredient': [
                            f'{ingredient_name} задан повторно.'
                        ]}
                    )
                else:
                    ingredients_id.add(id)
                    error.append({})
        if any(error):
            raise serializers.ValidationError(error)
        return value

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError(
                'Картинка не найдена.'
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

    def create(self, validated_data):
        request = self.context['request']
        validated_data['author'] = request.user
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
        try:
            tags = validated_data.pop('tags')
        except Exception:
            raise serializers.ValidationError(
                'Тэги отсутствуют.'
            )
        try:
            ingredients = validated_data.pop('ingredient_recipes')
        except Exception:
            raise serializers.ValidationError(
                'Ингредиенты отсутствуют.'
            )
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


class OptionUserSerializer(serializers.ModelSerializer):

    def validate(self, data):
        id = self.context['option_data']['recipe']
        user = self.context['option_data']['user']
        if not Recipe.objects.filter(id=id):
            raise serializers.ValidationError(
                'Рецепт не найден.'
            )
        if self.Meta.model.objects.filter(recipe=id, user=user):
            raise serializers.ValidationError(
                f'Не возможно добавить в {self.Meta.model._meta.verbose_name} '
                'повторно.'
            )
        data['user'] = user
        data['recipe'] = Recipe.objects.get(id=id)
        return data

    def to_representation(self, instance):
        return RecipeMinifieldSerialiser(instance.recipe).data

    class Meta:
        fields = ()
        # fields = ('id', 'name', 'image', 'cooking_time')
        # read_only_fields = ('id', 'name', 'image', 'cooking_time')


class FavoriteUserSerializer(OptionUserSerializer):

    class Meta(OptionUserSerializer.Meta):
        model = FavoriteUser


class ShoppingCartUserSerializer(OptionUserSerializer):

    class Meta(OptionUserSerializer.Meta):
        model = ShoppingCartUser


class SubscriptionUserSerializer(serializers.ModelSerializer):

    def validate(self, data):
        id = self.context['option_data']['author']
        user = self.context['option_data']['user']

        author = get_object_or_404(User, id=id)
        if SubscriptionUser.objects.filter(author=author, user=user):
            raise serializers.ValidationError(
                'Не возможно добавить подписку повторно.'
            )
        if user == author:
            raise serializers.ValidationError(
                'Невозможно подписаться на себя.'
            )
        data['user'] = user
        data['author'] = author
        return data

    def to_representation(self, instance):
        return UserWithRecipesSerializer(
            User.objects.annotate(recipes_count=Count('recipes')).get(
                id=instance.author.id
            ),
            context={'request': self.context['request']}
        ).data

    class Meta:
        model = SubscriptionUser
        fields = ()
