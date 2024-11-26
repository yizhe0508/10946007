# services/search_service.py
from django.db.models import Q
from ..models import SwapPost

class SwapPostSearchService:
    @staticmethod
    def search_posts(filters=None):
        """
        搜尋交換貼文
        filters: 包含 game_id, server_id, item_name 的字典
        """
        filters = filters or {}
        swap_posts = SwapPost.objects.filter(status='WAITING').order_by('-updated_at', '-created_at')
        
        if not filters:
            return swap_posts
            
        query = Q(status='WAITING')
        if filters.get('game_id'):
            query &= Q(game_id=int(filters['game_id']))
        if filters.get('server_id'):
            query &= Q(server_id=int(filters['server_id']))
        if filters.get('item_name'):
            query &= Q(item_name__icontains=filters['item_name'])
        
        return swap_posts.filter(query)