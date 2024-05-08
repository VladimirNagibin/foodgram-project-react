from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.paginations import LimitPageNumberPagination
from api.permissions import IsAuthenticatedOrAuthorOrReadOnly
from api.serializers import (IngredientSerialiser, RecipeMinifieldSerialiser,
                             RecipeSerialiser, TagSerialiser,
                             UserFavoriteSerializer,
                             UserIsSubscribedSerializer, UserSerializer,
                             UserSetPasswordSerialiser,
                             UserShoppingCartSerializer,
                             UserSubscribeSerializer,
                             UserWithRecipesSerializer)
from api.servises import get_pdf
from recipes.models import Ingredient, Recipe, Tag

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):

    queryset = User.objects.all()
    http_method_names = ('get', 'post')
    permission_classes = (AllowAny, )
    pagination_class = LimitPageNumberPagination

    def get_queryset(self):
        return User.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return UserSerializer
        return UserIsSubscribedSerializer

    @action(
        detail=False,
        methods=('GET', ),
        url_name='me',
        url_path='me',
        permission_classes=(IsAuthenticated, )
    )
    def get_self(self, request):
        """Функция для получения данных о себе."""
        serializer = UserIsSubscribedSerializer(
            request.user,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=('POST', ),
        url_name='set_password',
        url_path='set_password',
        permission_classes=(IsAuthenticated, )
    )
    def set_password(self, request):
        """Функция для изменения пароля."""
        serializer = UserSetPasswordSerialiser(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(('POST', 'DELETE'))
@permission_classes((IsAuthenticated, ))
def subscribe(request, **kwargs):
    """Вью отвечающая за подписку пользователей."""

    serializer = UserSubscribeSerializer(
        request.user,
        data=request.data,
        context={'request': request}
    )
    serializer.is_valid(raise_exception=True)
    if request.method == 'POST':
        serializer.save()
        return Response(
            UserWithRecipesSerializer(
                User.objects.annotate(
                    recipes_count=Count('recipes')
                ).prefetch_related(
                    'recipes'
                ).get(id=kwargs['id']), context={'request': request}
            ).data,
            status=status.HTTP_201_CREATED
        )
    else:
        request.user.subscriptions.remove(kwargs['id'])
        return Response(
            status=status.HTTP_204_NO_CONTENT
        )


class SubscriptionListViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):

    permission_classes = (IsAuthenticated,)
    pagination_class = LimitPageNumberPagination
    serializer_class = UserWithRecipesSerializer

    def get_queryset(self):
        return self.request.user.subscriptions.annotate(
            recipes_count=Count('recipes')
        ).prefetch_related(
            'recipes'
        ).order_by('username')


class TagViewSet(viewsets.ModelViewSet):

    queryset = Tag.objects.all()
    serializer_class = TagSerialiser
    permission_classes = (AllowAny,)
    pagination_class = None
    http_method_names = ('get')


class IngredientViewSet(viewsets.ModelViewSet):

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerialiser
    permission_classes = (AllowAny,)
    pagination_class = None
    filter_backends = (DjangoFilterBackend, )
    filterset_class = IngredientFilter
    http_method_names = ('get')


class RecipeViewSet(viewsets.ModelViewSet):

    serializer_class = RecipeSerialiser
    http_method_names = ('get', 'post', 'delete', 'patch')
    permission_classes = (IsAuthenticatedOrAuthorOrReadOnly, )
    pagination_class = LimitPageNumberPagination
    filter_backends = (DjangoFilterBackend, )
    filterset_class = RecipeFilter

    def get_queryset(self):
        return Recipe.objects.prefetch_related(
            'tags'
        ).prefetch_related(
            'ingredient_recipes'
        ).select_related(
            'author'
        )

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=False,
        methods=('POST', ),
        url_name='favorite',
        url_path=r'(?P<id>\d+)/favorite',
        permission_classes=(IsAuthenticated, ))
    def favorite_add(self, request, **kwargs):
        """Функция для добавления в избранное."""
        serializer = UserFavoriteSerializer(
            request.user,
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            RecipeMinifieldSerialiser(
                Recipe.objects.get(id=kwargs['id'])
            ).data,
            status=status.HTTP_201_CREATED
        )

    @favorite_add.mapping.delete
    def favorite_del(self, request, **kwargs):
        """Функция для удаления из избранного."""
        serializer = UserFavoriteSerializer(
            request.user,
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        request.user.favorites.remove(kwargs['id'])
        return Response(
            status=status.HTTP_204_NO_CONTENT
        )

    @action(
        detail=False,
        methods=('POST', ),
        url_name='shopping_cart',
        url_path=r'(?P<id>\d+)/shopping_cart',
        permission_classes=(IsAuthenticated, ))
    def shopping_cart_add(self, request, **kwargs):
        """Функция для добавления в список покупок."""
        serializer = UserShoppingCartSerializer(
            request.user,
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            RecipeMinifieldSerialiser(
                Recipe.objects.get(id=kwargs['id'])
            ).data,
            status=status.HTTP_201_CREATED
        )

    @shopping_cart_add.mapping.delete
    def shopping_cart_del(self, request, **kwargs):
        """Функция для удаления из списка покупок."""
        serializer = UserShoppingCartSerializer(
            request.user,
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        request.user.shopping_cart.remove(kwargs['id'])
        return Response(
            status=status.HTTP_204_NO_CONTENT
        )

    @action(
        detail=False,
        methods=('GET', ),
        url_name='download_shopping_cart',
        url_path='download_shopping_cart',
        permission_classes=(IsAuthenticated, ))
    def download_shopping_cart(self, request):
        """Функция для скачивания списка покупок."""
        recipes = request.user.shopping_cart.all()
        ingredients = recipes.prefetch_related(
            'ingredients'
        ).values(
            'ingredients__name',
            'ingredients__measurement_unit'
        ).annotate(amount=Sum('ingredient_recipes__amount')).order_by(
            'ingredients__name'
        )
        return get_pdf(ingredients, recipes, request.build_absolute_uri('/'))
