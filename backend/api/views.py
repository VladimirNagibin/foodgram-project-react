from django.db.models import Count, F, Sum
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.paginations import LimitPageNumberPagination
from api.permissions import IsAuthenticatedOrAuthorOrReadOnly
from api.serializers import (FavoriteUserSerializer, IngredientSerialiser,
                             RecipeCreateUpdateSerialiser,
                             RecipeReadSerialiser, ShoppingCartUserSerializer,
                             SubscriptionUserSerializer, TagSerialiser,
                             UserWithRecipesSerializer)
from api.servises import add_option_user, get_pdf, remove_option_user
from recipes.models import (FavoriteUser, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCartUser, Tag)
from users.models import SubscriptionUser, User


class UserViewSet(DjoserUserViewSet):

    pagination_class = LimitPageNumberPagination

    def get_permissions(self):
        if self.action == 'me':
            return (IsAuthenticated(),)
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
            data={'user': request.user.id, 'author': kwargs['id']},
            context={'request': request}
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
        subscr_user = SubscriptionUser.objects.filter(user=request.user,
                                                      author=kwargs['id'])
        if subscr_user.exists():
            subscr_user.delete()
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

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


class TagViewSet(viewsets.ReadOnlyModelViewSet):

    permission_classes = (AllowAny,)
    pagination_class = None
    queryset = Tag.objects.all()
    serializer_class = TagSerialiser


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):

    permission_classes = (AllowAny,)
    pagination_class = None
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerialiser
    filter_backends = (DjangoFilterBackend, )
    filterset_class = IngredientFilter


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
        if self.action in ('list', 'retrieve'):
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
