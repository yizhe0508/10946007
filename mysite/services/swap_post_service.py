# services/swap_post_service.py
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils.dateparse import parse_datetime 
from PIL import Image
from io import BytesIO
import logging
from ..models import Game, Server, SwapPost
from django.core.paginator import Paginator
from django.utils import timezone

logger = logging.getLogger(__name__)

class SwapPostService:
    @staticmethod
    def validate_post_data(data):
        required_fields = ['game_id', 'server_id', 'item_name', 'item_description', 
                         'desired_item', 'swap_time', 'swap_location', 'role_name']
        
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return False, '所有欄位都是必填的！'
            
        try:
            game = Game.objects.get(id=data['game_id'])
            server = Server.objects.get(id=data['server_id'], game=game)
        except Game.DoesNotExist:
            return False, '選擇的遊戲不存在。'
        except Server.DoesNotExist:
            return False, '選擇的伺服器不存在。'
            
        return True, None

    @staticmethod
    def process_image(image_file, item_name):
        if not image_file:
            return None
            
        try:
            img = Image.open(image_file)
            if img.mode == 'RGBA':
                img = img.convert('RGB')
                
            output = BytesIO()
            img.save(output, format='JPEG', quality=85)
            
            return InMemoryUploadedFile(
                output, 'ImageField', 
                f'{item_name}.jpg', 
                'image/jpeg', 
                output.tell(), 
                None
            )
        except Exception as e:
            logger.error(f"處理圖片時發生錯誤: {str(e)}")
            return None

    @staticmethod
    def create_swap_post(user, data, image=None):
        try:
            processed_image = SwapPostService.process_image(image, data['item_name']) if image else None
            
            swap_post = SwapPost.objects.create(
                user=user,
                game_id=data['game_id'],
                server_id=data['server_id'],
                item_name=data['item_name'],
                item_image=processed_image,
                item_description=data['item_description'],
                desired_item=data['desired_item'],
                swap_time=parse_datetime(data['swap_time']),
                swap_location=data['swap_location'],
                role_name=data['role_name'],
                status='WAITING'
            )
            return True, '交換貼文已成功新增！'
        except Exception as e:
            logger.error(f"創建交換貼文時發生錯誤: {str(e)}")
            return False, f'發生錯誤: {str(e)}'
    
    @staticmethod
    def update_swap_post(post, data, image=None):
        try:
            # 驗證數據
            is_valid, error_message = SwapPostService.validate_post_data(data)
            if not is_valid:
                return False, error_message

            # 處理圖片
            if image:
                processed_image = SwapPostService.process_image(image, data['item_name'])
                if processed_image:
                    post.item_image = processed_image

            # 更新資料
            post.game_id = data['game_id']
            post.server_id = data['server_id']
            post.item_name = data['item_name']
            post.item_description = data['item_description']
            post.desired_item = data['desired_item']
            post.swap_time = parse_datetime(data['swap_time'])
            post.swap_location = data['swap_location']
            post.role_name = data['role_name']
            post.save()

            return True, '交換貼文已成功更新！'
        except Exception as e:
            logger.error(f"更新交換貼文時發生錯誤: {str(e)}")
            return False, f'發生錯誤: {str(e)}'

    @staticmethod
    def delete_swap_post(post, user):
        """
        刪除交換貼文
        使用模型的 can_delete 方法進行權限驗證
        """
        try:
            if post.can_delete(user):
                post.delete()
                return True, '貼文已成功刪除。'
            else:
                return False, '只能刪除待交換狀態的貼文。'
        except Exception as e:
            logger.error(f"刪除交換貼文時發生錯誤: {str(e)}")
            return False, f'刪除貼文時發生錯誤: {str(e)}'

    @staticmethod
    def update_status(post, new_status, user):
        try:
            if new_status not in dict(SwapPost.STATUS_CHOICES).keys():
                return False, '無效的狀態。'

            if not post.can_update_status(user):
                return False, '您沒有權限更新此貼文狀態。'

            post.status = new_status
            post.save()
            return True, '交換狀態已更新。'
        except Exception as e:
            logger.error(f"更新貼文狀態時發生錯誤: {str(e)}")
            return False, f'發生錯誤: {str(e)}'

    @staticmethod
    def get_managed_posts(user, post_type='my_posts', page_number=1, per_page=5):
        """獲取使用者管理的貼文"""
        try:
            if post_type == 'participated_posts':
                posts = SwapPost.objects.filter(swapper=user)
            else:
                posts = SwapPost.objects.filter(user=user)
            
            posts = posts.order_by('-updated_at', '-created_at')
            paginator = Paginator(posts, per_page)
            return paginator.get_page(page_number), None
            
        except Exception as e:
            logger.error(f"獲取管理貼文時發生錯誤: {str(e)}")
            return None, str(e)

    @staticmethod
    def update_post_time(post):
        """更新貼文時間"""
        try:
            post.updated_at = timezone.now()
            post.save()
            formatted_time = timezone.localtime(post.updated_at).strftime("%Y/%m/%d %H:%M")
            return True, formatted_time
        except Exception as e:
            logger.error(f"更新貼文時間時發生錯誤: {str(e)}")
            return False, str(e)    