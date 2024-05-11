from django.db.models import Count
from django.shortcuts import get_object_or_404
from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.constants import (AMOUNT_MAX_VALUE, AMOUNT_MIN_VALUE,
                               COOKING_MAX_TIME, COOKING_MIN_TIME)
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
        request = self.context['request']
        if request and request.query_params.get('recipes_limit'):
            recipes_user = recipes_user[:int(
                request.query_params.get('recipes_limit')
            )]
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


class RecipeMinifieldSerialiser(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class IngredientRecipeReadSerialiser(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient_id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientRecipeCreateUpdateSerialiser(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(source='ingredient',
                                            queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(max_value=AMOUNT_MAX_VALUE,
                                      min_value=AMOUNT_MIN_VALUE)

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')


class RecipeReadSerialiser(serializers.ModelSerializer):

    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    tags = TagSerialiser(many=True)
    author = UserSerializer()
    ingredients = IngredientRecipeReadSerialiser(
        many=True,
        source='ingredient_recipes',
    )

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time', 'tags', 'author',
                  'ingredients', 'is_favorited', 'is_in_shopping_cart', 'text')
        read_only_fields = ('id', 'name', 'image', 'cooking_time', 'tags',
                            'author', 'ingredients', 'is_favorited',
                            'is_in_shopping_cart', 'text')

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


class RecipeCreateUpdateSerialiser(serializers.ModelSerializer):

    image = Base64ImageField(allow_empty_file=False, allow_null=False)
    cooking_time = serializers.IntegerField(min_value=COOKING_MIN_TIME,
                                            max_value=COOKING_MAX_TIME)
    tags = serializers.PrimaryKeyRelatedField(many=True,
                                              queryset=Tag.objects.all())
    ingredients = IngredientRecipeCreateUpdateSerialiser(
        many=True,
        source='ingredient_recipes'
    )

    class Meta:
        model = Recipe
        fields = ('name', 'image', 'cooking_time', 'tags', 'ingredients',
                  'text')

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                [{'ingredient': ['Ингредиенты отсутствуют.']}]
            )
        if (len(set([ingr['ingredient'] for ingr in value])) < len(value)):
            raise serializers.ValidationError(
                [{'ingredient': ['Ингредиенты повторяются.']}]
            )
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

    def set_tags_ingredients_in_recipe(self, recipe, tags, ingredients):
        recipe.tags.set(tags)
        IngredientRecipe.objects.bulk_create(
            [IngredientRecipe(recipe=recipe,
                              ingredient=ingr['ingredient'],
                              amount=ingr['amount']) for ingr in ingredients]
        )

    def create(self, validated_data):
        request = self.context['request']
        validated_data['author'] = request.user
        ingredients = validated_data.pop('ingredient_recipes')
        tags = validated_data.pop('tags')
        recipe = super().create(validated_data)
        self.set_tags_ingredients_in_recipe(recipe, tags, ingredients)
        return recipe

    def update(self, instance, validated_data, **kwargs):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredient_recipes')
        instance = super().update(instance, validated_data)
        instance.tags.clear()
        instance.ingredients.clear()
        self.set_tags_ingredients_in_recipe(instance, tags, ingredients)
        return instance

    def to_representation(self, instance):
        serializer = RecipeReadSerialiser(
            instance, context={'request': self.context['request']}
        )
        return serializer.data


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
