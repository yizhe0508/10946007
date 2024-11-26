# services/message_service.py
import logging
from ..models import SwapMessage

logger = logging.getLogger(__name__)

class MessageService:
    @staticmethod
    def send_message(swap_post, sender, content):
        """發送交換訊息"""
        try:
            if not content:
                return False, '訊息內容不能為空'

            message = SwapMessage.objects.create(
                swap_post=swap_post,
                sender=sender,
                content=content
            )
            
            return True, {
                'id': message.id,
                'sender': message.sender.username,
                'content': message.content,
                'created_at': message.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            logger.error(f"發送訊息時發生錯誤: {str(e)}")
            return False, str(e)

    @staticmethod
    def get_messages(swap_post, last_message_id=None):
        """獲取交換訊息"""
        try:
            messages = swap_post.messages.all()
            if last_message_id:
                messages = messages.filter(id__gt=last_message_id)
                
            return True, [{
                'id': msg.id,
                'sender': msg.sender.username,
                'content': msg.content,
                'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
            } for msg in messages]
        except Exception as e:
            logger.error(f"獲取訊息時發生錯誤: {str(e)}")
            return False, str(e)