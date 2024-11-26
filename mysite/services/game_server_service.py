# services/game_server_service.py
from ..models import Game, Server

class GameService:
    @staticmethod
    def get_all_games():
        """
        獲取所有遊戲
        """
        return Game.objects.all()

    @staticmethod
    def get_servers_for_game(game_id):
        """
        獲取指定遊戲的所有伺服器
        """
        if not game_id:
            return []
        return Server.objects.filter(game_id=game_id)