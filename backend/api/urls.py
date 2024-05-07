from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from api.views import (IngredientViewSet, RecipeViewSet,
                       SubscriptionListViewSet, TagViewSet, UserViewSet,
                       subscribe)

router = DefaultRouter()
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register(
    'users/subscriptions', SubscriptionListViewSet, basename='subscriptions'
)
router.register('users', UserViewSet, basename='users')

urlpatterns = [
    re_path(
        r'users/(?P<id>\d+)/subscribe/', subscribe, name='subscribes'
    ),
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
