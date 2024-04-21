from django.contrib.auth import get_user_model
from django.db.models import Avg
from django.shortcuts import get_object_or_404
# from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action  # , api_view # permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

# from .filters import TitleFilter
# from .permissions import (IsAdminOrSuperUserOnly, IsAdminOrAuthorOrReadOnly,
#                          IsAdminOrReadOnly)
from .paginations import LimitPageNumberPagination
from .serializers import (
    IngredientSerialiser,
    UserSerializer,
    UserSetPasswordSerialiser,
    TagSerialiser
)
from recipes.models import Ingredient, Tag

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет отвечающий за работу с моделью User."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    http_method_names = ('get', 'post')
    permission_classes = (IsAuthenticated, )
    pagination_class = LimitPageNumberPagination
    # filter_backends = (filters.SearchFilter, )
    # search_fields = ('username', )
    # lookup_field = 'username'

    @action(
        detail=False,
        methods=('GET', ),
        url_name='me',
        url_path='me',
        permission_classes=(IsAuthenticated, )
    )
    def get_self(self, request):
        """Функция позволяющая получить данные о себе."""
        serializer = UserSerializer(request.user)
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


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerialiser
    permission_classes = (AllowAny,)
    pagination_class = None
    # filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    # filterset_class = TitleFilter
    # ordering_fields = ('name', 'year')
    # ordering = ('name',)
    http_method_names = ('get')


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerialiser
    permission_classes = (AllowAny,)
    pagination_class = None
    # filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    # filterset_class = TitleFilter
    # ordering_fields = ('name', 'year')
    # ordering = ('name',)
    http_method_names = ('get')
