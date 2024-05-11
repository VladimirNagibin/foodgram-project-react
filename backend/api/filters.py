from django_filters import CharFilter, ChoiceFilter, ModelMultipleChoiceFilter
from django_filters.rest_framework import FilterSet

from recipes.constants import BOOL_CHOICES
from recipes.models import Ingredient, Recipe, Tag


class RecipeFilter(FilterSet):

    tags = ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
        label='Tags'
    )
    is_favorited = ChoiceFilter(
        choices=BOOL_CHOICES,
        method='filter_is_favorited'
    )
    is_in_shopping_cart = ChoiceFilter(
        choices=BOOL_CHOICES,
        method='filter_is_in_shopping_cart',
    )

    class Meta:
        model = Recipe
        fields = ('is_favorited', 'is_in_shopping_cart', 'author', 'tags')

    def filter_is_favorited(self, queryset, name, value):
        if int(value) and self.request.user.is_authenticated:
            return queryset.filter(favorite_users__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if int(value) and self.request.user.is_authenticated:
            return queryset.filter(shopping_cart_user__user=self.request.user)
        return queryset


class IngredientFilter(FilterSet):

    name = CharFilter(method='filter_name')

    class Meta:
        model = Ingredient
        fields = ('name', )

    def filter_name(self, queryset, name, value):
        return queryset.filter(name__istartswith=value)
