# services/pagination_service.py
from django.core.paginator import Paginator

class PaginationService:
    def __init__(self, items_per_page=5):
        self.items_per_page = items_per_page

    def paginate_queryset(self, queryset, page_number):
        """
        對查詢結果進行分頁
        """
        paginator = Paginator(queryset, self.items_per_page)
        return paginator.get_page(page_number)