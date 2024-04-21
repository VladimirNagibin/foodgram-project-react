from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import IngredientViewSet, TagViewSet, UserViewSet

router_v1 = DefaultRouter()
# router_v1.register(r'titles/(?P<title_id>\d+)/reviews', ReviewViewSet,
#                   basename='reviews')
# router_v1.register(
#    r'titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)/comments',
#    CommentViewSet, basename='comments'
# )

router_v1.register('users', UserViewSet, basename='users')
router_v1.register('tags', TagViewSet, basename='tags')
router_v1.register('ingredients', IngredientViewSet, basename='ingredients')

# auth_urls = [
#    path('signup/', signup, name='registration'),
#    path('token/', get_token, name='token'),
# ]

urlpatterns = [
    path('', include(router_v1.urls)),
    path('auth/', include('djoser.urls.authtoken'))
    # path('v1/auth/', include(auth_urls))
]
