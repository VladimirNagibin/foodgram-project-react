from rest_framework.pagination import PageNumberPagination

from users.constants import MAX_PAGE_SIZE


class LimitPageNumberPagination(PageNumberPagination):
    page_size_query_param = 'limit'
    max_page_size = MAX_PAGE_SIZE
