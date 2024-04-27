from pprint import pprint

from django.contrib.auth import get_user_model
from django.core.files import File
from django.db.models import Count, Exists, OuterRef, Subquery, Sum, Value
from django.db.models import BooleanField, ExpressionWrapper, Q
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action  # , api_view # permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .filters import IngredientFilter, RecipeFilter
from .permissions import (IsAuthenticatedOrAuthorOrReadOnly, )
from .paginations import LimitPageNumberPagination
from .serializers import (
    IngredientSerialiser,
    UserFavoriteSerializer,
    UserIsSubscribedSerializer,
    UserSerializer,
    UserSetPasswordSerialiser,
    UserShoppingCartSerializer,
    UserSubscribeSerializer,
    RecipeSerialiser,
    SubscriptionRecipeSerialiser,
    SubscriptionSerializer,
    TagSerialiser,
)
from recipes.models import Ingredient, Recipe, Tag

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):

    queryset = User.objects.all()
    http_method_names = ('get', 'post', 'delete')
    permission_classes = (AllowAny, )
    pagination_class = LimitPageNumberPagination

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
        """Функция позволяющая получить данные о себе."""
        serializer = UserIsSubscribedSerializer(request.user, context={'request': request})
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

    @action(
        detail=False,
        methods=('POST', ),
        url_name='subscribe',
        url_path=r'(?P<user_id>\d+)/subscribe',
        permission_classes=(IsAuthenticated, ))
    def subscribe(self, request, **kwargs):
        """Функция для подписки."""
        author = get_object_or_404(User.objects.annotate(
            recipes_count=Count('recipes')
        ).annotate(is_subscribed=Value(True)).prefetch_related(
            'recipes'
        ).order_by('username'), pk=kwargs['user_id'])
        serializer = UserSubscribeSerializer(
            request.user,
            data=request.data,
            context={'author': author, 'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            SubscriptionSerializer(author, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    @subscribe.mapping.delete
    def del_subscribe(self, request, **kwargs):
        """Функция для отмены подписки."""
        author = get_object_or_404(User, pk=kwargs['user_id'])
        serializer = UserSubscribeSerializer(
            request.user,
            data=request.data,
            context={'author': author, 'request': request}
        )
        serializer.is_valid(raise_exception=True)
        request.user.subscription.remove(author)
        return Response(
            status=status.HTTP_204_NO_CONTENT
        )


class SubscriptionListViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):

    permission_classes = (IsAuthenticated,)
    pagination_class = LimitPageNumberPagination
    serializer_class = SubscriptionSerializer

    def get_queryset(self):
        return self.request.user.subscription.annotate(
                recipes_count=Count('recipes')
            ).annotate(is_subscribed=Value(True)).prefetch_related(
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
    #http_method_names = ('get', 'post', 'delete', 'patch')
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
            #).annotate(
                #is_favorited=ExpressionWrapper(
                #    Q(favorite_users=user_id),
                #    output_field=BooleanField(),
                #)
            #    is_favorited=Exists(
            #        Recipe.objects.prefetch_related(
            #           'favorite_users'
            #        ).filter(favorite_users=user_id, id=OuterRef('id'))
            #    )
            #).annotate(
            #    is_in_shopping_cart=Exists(
            #        Subquery(
            #            Recipe.objects.prefetch_related(
            #                'shopping_cart_users'
            #            ).filter(shopping_cart_users=user_id, id=OuterRef('id'))
            #        )
            #    )
            #)

        #if self.request.user and self.request.user.is_authenticated:
            #recipe_queryset = recipe_queryset.annotate(
            #    is_favorited=Exists(
            #        Subquery(
            #            self.request.user.favorite.all().filter(id=OuterRef(
            #                'id'
            #            ))
            #        )
            #    )
            #).annotate(
            #    is_in_shopping_cart=Exists(
            #        Subquery(
            #            self.request.user.shopping_cart.all().filter(
            #                id=OuterRef('id')
            #            )
            #        )
            #    )
            #)
        #else:
        #    recipe_queryset = recipe_queryset.annotate(
        #        is_favorited=Value(False)
        #    ).annotate(
        #        is_in_shopping_cart=Value(False)
        #    )
        #return recipe_queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.serializer_class(
            instance,
            data=request.data,
            context={'request': request},
            partial=False
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(
        detail=False,
        methods=('POST', ),
        url_name='favorite',
        url_path=r'(?P<recipe_id>\d+)/favorite',
        permission_classes=(IsAuthenticated, ))
    def favorite_add(self, request, **kwargs):
        """Функция для добавления в избранное."""
        #recipe = get_object_or_404(Recipe, pk=kwargs['recipe_id'])
        serializer = UserFavoriteSerializer(
            request.user,
            data=request.data,
            context={'recipe': kwargs['recipe_id'], 'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            SubscriptionRecipeSerialiser(
                get_object_or_404(Recipe, pk=kwargs['recipe_id']), context={'request': request}
            ).data,
            status=status.HTTP_201_CREATED
        )

    @favorite_add.mapping.delete
    def favorite_del(self, request, **kwargs):
        """Функция для отмены подписки."""
        recipe = get_object_or_404(Recipe, pk=kwargs['recipe_id'])
        serializer = UserFavoriteSerializer(
            request.user,
            data=request.data,
            context={'recipe': recipe, 'request': request}
        )
        serializer.is_valid(raise_exception=True)
        request.user.favorite.remove(recipe)
        return Response(
            status=status.HTTP_204_NO_CONTENT
        )

    @action(
        detail=False,
        methods=('POST', ),
        url_name='shopping_cart',
        url_path=r'(?P<recipe_id>\d+)/shopping_cart',
        permission_classes=(IsAuthenticated, ))
    def shopping_cart_add(self, request, **kwargs):
        """Функция для добавления в список покупок."""
        #recipe = get_object_or_404(Recipe, pk=kwargs['recipe_id'])
        serializer = UserShoppingCartSerializer(
            request.user,
            data=request.data,
            context={'recipe': kwargs['recipe_id'], 'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            SubscriptionRecipeSerialiser(
                get_object_or_404(Recipe, pk=kwargs['recipe_id']), context={'request': request}
            ).data,
            status=status.HTTP_201_CREATED
        )

    @shopping_cart_add.mapping.delete
    def shopping_cart_del(self, request, **kwargs):
        """Функция для удаления из списка покупок."""
        recipe = get_object_or_404(Recipe, pk=kwargs['recipe_id'])
        serializer = UserShoppingCartSerializer(
            request.user,
            data=request.data,
            context={'recipe': recipe, 'request': request}
        )
        serializer.is_valid(raise_exception=True)
        request.user.shopping_cart.remove(recipe)
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
        ingredients = request.user.shopping_cart.prefetch_related(
            'ingredients'
        ).values(
            'ingredients__name',
            'ingredients__measurement_unit'
        ).annotate(amount=Sum('ingredient_recipes__amount')).order_by(
            'ingredients__name'
        )
        with open('upload/Hello.txt', 'w') as f:
            myfile = File(f)
            for ingredient in ingredients:
                myfile.write(f'{ingredient["ingredients__name"]}, '
                             f'{ingredient["ingredients__measurement_unit"]} '
                             f'кол-во: {ingredient["amount"]}\n')
        myfile.closed
        try:
            file = open('upload/Hello.txt', 'rb')
            response = FileResponse(file, as_attachment=True)
            response['Content-Disposition'] = 'attachment; filename="Hello.txt"'
            return response
        except FileNotFoundError:
            return Response(
                status=status.HTTP_404_NOT_FOUND
            )
