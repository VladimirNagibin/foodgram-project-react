from django.contrib.auth import get_user_model
from django.db.models import Count, Sum, Value
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.paginations import LimitPageNumberPagination
from api.permissions import IsAuthenticatedOrAuthorOrReadOnly
from api.serializers import (IngredientSerialiser, RecipeSerialiser,
                             SubscriptionRecipeSerialiser,
                             SubscriptionSerializer, TagSerialiser,
                             UserFavoriteSerializer,
                             UserIsSubscribedSerializer, UserSerializer,
                             UserSetPasswordSerialiser,
                             UserShoppingCartSerializer,
                             UserSubscribeSerializer)
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
        ), pk=kwargs['user_id'])
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
        request.user.subscriptions.remove(author)
        return Response(
            status=status.HTTP_204_NO_CONTENT
        )


class SubscriptionListViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):

    permission_classes = (IsAuthenticated,)
    pagination_class = LimitPageNumberPagination
    serializer_class = SubscriptionSerializer

    def get_queryset(self):
        return self.request.user.subscriptions.annotate(
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
        serializer = UserFavoriteSerializer(
            request.user,
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            SubscriptionRecipeSerialiser(
                Recipe.objects.get(id=kwargs['recipe_id'])
            ).data,
            status=status.HTTP_201_CREATED
        )

    @favorite_add.mapping.delete
    def favorite_del(self, request, **kwargs):
        """Функция для отмены подписки."""
        serializer = UserFavoriteSerializer(
            request.user,
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        request.user.favorites.remove(kwargs['recipe_id'])
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
        serializer = UserShoppingCartSerializer(
            request.user,
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            SubscriptionRecipeSerialiser(
                Recipe.objects.get(id=kwargs['recipe_id'])
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
        request.user.shopping_cart.remove(kwargs['recipe_id'])
        return Response(
            status=status.HTTP_204_NO_CONTENT
        )

    def get_pdf(self, user, link):
        ingredients = user.shopping_cart.prefetch_related(
            'ingredients'
        ).values(
            'ingredients__name',
            'ingredients__measurement_unit'
        ).annotate(amount=Sum('ingredient_recipes__amount')).order_by(
            'ingredients__name'
        )
        pdfmetrics.registerFont(
            TTFont('DejaVuSerif', 'DejaVuSerif.ttf', 'UTF-8')
        )
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = ('attachment;'
                                           'filename="ingredients.pdf"')
        y_start = 600
        y = 750
        x = 100
        x_start = 10
        size = 1
        size_recipe = 0.5
        step = 20
        step_big = 50
        font = 20
        font_big = 50
        font_middle = 25
        max_length = 40
        head_length = 5
        logo_path = '../static/logo192.png'
        p = canvas.Canvas(response)
        try:
            p.drawImage(
                ImageReader(logo_path), x_start, y, size * inch, size * inch
            )
        except Exception:
            ...
        p.setFont("DejaVuSerif", font_big)
        p.drawString(x, y, 'FOODGRAM')
        p.linkURL(
            link,
            (x, y, x + head_length * inch, y + step_big),
            relative=1
        )
        y -= step_big
        p.setFont("DejaVuSerif", font_middle)
        p.drawString(x_start, y, "Для приготовления выбранных блюд:")
        y -= step_big
        p.setFont("DejaVuSerif", font)
        for recipe in user.shopping_cart.all():
            image = ImageReader(recipe.image)
            p.drawImage(
                image,
                x_start + step,
                y,
                size_recipe * inch,
                size_recipe * inch,
            )
            p.drawString(
                x, y, f'{recipe.name[:max_length]}'
            )
            y -= step_big
            if y <= 0:
                y = y_start
                p.showPage()
                p.setFont("DejaVuSerif", font)
        p.setFont("DejaVuSerif", font_middle)
        p.drawString(x_start, y, "Требуются следующие ингредиенты:")
        y -= step_big
        if y <= 0:
            y = y_start
            p.showPage()
        p.setFont("DejaVuSerif", font)
        for ingredient in ingredients:
            p.drawString(
                x, y,
                (f'{ingredient["ingredients__name"]}, '
                 f'{ingredient["amount"]} '
                 f'{ingredient["ingredients__measurement_unit"]}')
            )
            y -= step
            if y <= 0:
                y = y_start
                p.showPage()
                p.setFont("DejaVuSerif", font)

        p.showPage()
        p.save()
        return response

    @action(
        detail=False,
        methods=('GET', ),
        url_name='download_shopping_cart',
        url_path='download_shopping_cart',
        permission_classes=(IsAuthenticated, ))
    def download_shopping_cart(self, request):
        """Функция для скачивания списка покупок."""
        
        return self.get_pdf(request.user, request.build_absolute_uri('/'))
