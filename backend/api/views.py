from django.db.models import Count, F, Sum
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from api.filters import IngredientFilter, RecipeFilter
from api.paginations import LimitPageNumberPagination
from api.permissions import IsAuthenticatedOrAuthorOrReadOnly
from api.serializers import (FavoriteUserSerializer, IngredientSerialiser,
                             RecipeCreateUpdateSerialiser,
                             RecipeReadSerialiser, ShoppingCartUserSerializer,
                             SubscriptionUserSerializer, TagSerialiser,
                             UserWithRecipesSerializer)
from api.servises import get_pdf
from recipes.models import (FavoriteUser, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCartUser, Tag)
from users.models import SubscriptionUser, User


class UserViewSet(DjoserUserViewSet):

    pagination_class = LimitPageNumberPagination

    def get_permissions(self):
        if self.action == 'me':
            self.permission_classes = (IsAuthenticated,)
        return super().get_permissions()

    @action(
        detail=False,
        methods=('POST', ),
        url_name='subscribe',
        url_path=r'(?P<id>\d+)/subscribe',
        permission_classes=(IsAuthenticated, ))
    def subscribe(self, request, **kwargs):
        """Функция для подписки."""
        serializer = SubscriptionUserSerializer(
            data=request.data,
            context={
                'request': request,
                'option_data': {'user': request.user, 'author': kwargs['id']}
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    @subscribe.mapping.delete
    def del_subscribe(self, request, **kwargs):
        """Функция для отмены подписки."""
        author = get_object_or_404(User, id=kwargs['id'])
        if SubscriptionUser.objects.filter(user=request.user, author=author):
            SubscriptionUser.objects.get(user=request.user,
                                         author=kwargs['id']).delete()
        else:
            raise ValidationError(
                'Запись для удаления подписки ещё не добавлена.'
            )
        return Response(
            status=status.HTTP_204_NO_CONTENT
        )

    @action(
        detail=False,
        methods=('GET', ),
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        """Функция для вывода списка подписок"""
        serializer = UserWithRecipesSerializer(
            self.paginate_queryset(User.objects.filter(
                subscribers__user=request.user
            ).annotate(
                recipes_count=Count('recipes')
            ).prefetch_related(
                'recipes'
            ).order_by('username')),
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class ListRetriveViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                         viewsets.GenericViewSet):
    permission_classes = (AllowAny,)
    pagination_class = None


class TagViewSet(ListRetriveViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerialiser


class IngredientViewSet(ListRetriveViewSet):

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerialiser
    filter_backends = (DjangoFilterBackend, )
    filterset_class = IngredientFilter


def add_option_user(option_serializer, pk, request):
    serializer = option_serializer(
        data=request.data,
        context={
            'option_data': {'user': request.user, 'recipe': pk}
        },
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(
        serializer.data,
        status=status.HTTP_201_CREATED
    )


def remove_option_user(option_model, pk, request):
    recipe = get_object_or_404(Recipe, id=pk)
    if option_model.objects.filter(user=request.user, recipe=recipe):
        option_model.objects.get(user=request.user,
                                 recipe=recipe).delete()
    else:
        raise ValidationError(
            'Запись для удаления ещё не добавлена.'
        )
    return Response(
        status=status.HTTP_204_NO_CONTENT
    )


class RecipeViewSet(viewsets.ModelViewSet):

    http_method_names = ('get', 'post', 'delete', 'patch')
    permission_classes = (IsAuthenticatedOrAuthorOrReadOnly, )
    pagination_class = LimitPageNumberPagination
    filter_backends = (DjangoFilterBackend, )
    filterset_class = RecipeFilter

    def get_queryset(self):
        return Recipe.objects.prefetch_related(
            'tags', 'ingredient_recipes'
        ).select_related(
            'author'
        )

    def get_serializer_class(self):
        if self.action == 'list' or self.action == 'retrieve':
            return RecipeReadSerialiser
        return RecipeCreateUpdateSerialiser

    @action(
        detail=False,
        methods=('POST', ),
        url_name='favorite',
        url_path=r'(?P<id>\d+)/favorite',
        permission_classes=(IsAuthenticated, ))
    def favorite_add(self, request, **kwargs):
        """Функция для добавления в избранное."""
        return add_option_user(FavoriteUserSerializer, kwargs['id'], request)

    @favorite_add.mapping.delete
    def favorite_del(self, request, **kwargs):
        """Функция для удаления из избранного."""
        return remove_option_user(FavoriteUser, kwargs['id'], request)

    @action(
        detail=False,
        methods=('POST', ),
        url_name='shopping_cart',
        url_path=r'(?P<id>\d+)/shopping_cart',
        permission_classes=(IsAuthenticated, ))
    def shopping_cart_add(self, request, **kwargs):
        """Функция для добавления в список покупок."""
        return add_option_user(ShoppingCartUserSerializer,
                               kwargs['id'],
                               request)

    @shopping_cart_add.mapping.delete
    def shopping_cart_del(self, request, **kwargs):
        """Функция для удаления из списка покупок."""
        return remove_option_user(ShoppingCartUser, kwargs['id'], request)

    @action(
        detail=False,
        methods=('GET', ),
        permission_classes=(IsAuthenticated, ))
    def download_shopping_cart(self, request):
        """Функция для скачивания списка покупок."""
        return get_pdf(
            IngredientRecipe.objects.filter(
                recipe__shopping_cart_user__user=request.user
            ).values(
                name=F('ingredient__name'),
                measurement_unit=F('ingredient__measurement_unit')
            ).annotate(amount=Sum('amount')).order_by(
                'name'
            ),
            Recipe.objects.filter(shopping_cart_user__user=request.user),
            request.build_absolute_uri('/')
        )
