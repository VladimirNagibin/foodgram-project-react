from django.db.models import Count
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.constants import (AMOUNT_MAX_VALUE, AMOUNT_MIN_VALUE,
                               COOKING_MAX_TIME, COOKING_MIN_TIME)
from recipes.models import (FavoriteUser, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCartUser, Tag)
from users.models import SubscriptionUser, User


class UserSerializer(serializers.ModelSerializer):

    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        request = self.context['request']
        return bool(request and request.user.is_authenticated
                    and request.user.authors.filter(author=obj))


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
        recipes_user = obj.recipes.all()
        try:
            recipes_limit = int(
                self.context['request'].query_params.get('recipes_limit')
            )
        except Exception:
            recipes_limit = 0

        if recipes_limit:
            recipes_user = recipes_user[:recipes_limit]
        return RecipeMinifieldSerialiser(recipes_user,
                                         many=True,
                                         context=self.context).data


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
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(max_value=AMOUNT_MAX_VALUE,
                                      min_value=AMOUNT_MIN_VALUE)

    class Meta:
        model = Ingredient
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
                    and request.user.favorite_users.filter(recipe=obj))

    def get_is_in_shopping_cart(self, obj):
        request = self.context['request']
        return bool(request and request.user.is_authenticated
                    and request.user.shopping_cart_user.filter(recipe=obj))


class RecipeCreateUpdateSerialiser(serializers.ModelSerializer):

    image = Base64ImageField(allow_empty_file=False, allow_null=False)
    cooking_time = serializers.IntegerField(min_value=COOKING_MIN_TIME,
                                            max_value=COOKING_MAX_TIME)
    tags = serializers.PrimaryKeyRelatedField(many=True,
                                              queryset=Tag.objects.all())
    ingredients = IngredientRecipeCreateUpdateSerialiser(many=True)

    class Meta:
        model = Recipe
        fields = ('name', 'image', 'cooking_time', 'tags', 'ingredients',
                  'text')

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                [{'ingredient': ['Ингредиенты отсутствуют.']}]
            )
        if (len(set([ingr['id'] for ingr in value])) < len(value)):
            raise serializers.ValidationError(
                [{'ingredient': ['Ингредиенты повторяются.']}]
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

    @staticmethod
    def set_tags_ingredients_in_recipe(recipe, tags, ingredients):
        recipe.tags.set(tags)
        IngredientRecipe.objects.bulk_create(
            [IngredientRecipe(recipe=recipe,
                              ingredient=ingr['id'],
                              amount=ingr['amount']) for ingr in ingredients]
        )

    def create(self, validated_data):
        request = self.context['request']
        validated_data['author'] = request.user
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = super().create(validated_data)
        self.set_tags_ingredients_in_recipe(recipe, tags, ingredients)
        return recipe

    def update(self, instance, validated_data, **kwargs):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        super().update(instance, validated_data)
        instance.tags.clear()
        instance.ingredients.clear()
        self.set_tags_ingredients_in_recipe(instance, tags, ingredients)
        return instance

    def to_representation(self, instance):
        serializer = RecipeReadSerialiser(
            instance, context=self.context
        )
        return serializer.data


class OptionUserSerializer(serializers.ModelSerializer):

    def validate(self, data):
        if self.Meta.model.objects.filter(recipe=data['recipe'],
                                          user=data['user']):
            raise serializers.ValidationError(
                f'Не возможно добавить в {self.Meta.model._meta.verbose_name} '
                'повторно.'
            )
        return data

    class Meta:
        fields = ('recipe', 'user')

    def to_representation(self, instance):
        return RecipeMinifieldSerialiser(instance.recipe,
                                         context=self.context).data


class FavoriteUserSerializer(OptionUserSerializer):

    class Meta(OptionUserSerializer.Meta):
        model = FavoriteUser


class ShoppingCartUserSerializer(OptionUserSerializer):

    class Meta(OptionUserSerializer.Meta):
        model = ShoppingCartUser


class SubscriptionUserSerializer(serializers.ModelSerializer):

    def validate(self, data):
        author = data['author']
        user = data['user']

        if SubscriptionUser.objects.filter(author=author, user=user):
            raise serializers.ValidationError(
                'Не возможно добавить подписку повторно.'
            )
        if user == author:
            raise serializers.ValidationError(
                'Невозможно подписаться на себя.'
            )
        return data

    class Meta:
        model = SubscriptionUser
        fields = ('author', 'user')

    def to_representation(self, instance):
        return UserWithRecipesSerializer(
            User.objects.annotate(recipes_count=Count('recipes')).get(
                id=instance.author.id
            ),
            context=self.context
        ).data
