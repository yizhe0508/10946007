# services/swap_progress_service.py
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class SwapProgressService:
    @staticmethod
    def join_swap(post, user):
        """參與交換"""
        try:
            if post.status != 'WAITING':
                return False, '此貼文已不可參與交換。'
            if user == post.user:
                return False, '不能參與自己的交換。'
                
            post.status = 'IN_PROGRESS'
            post.swapper = user
            post.save()
            return True, '您已成功加入交換!'
        except Exception as e:
            logger.error(f"加入交換時發生錯誤: {str(e)}")
            return False, str(e)

    @staticmethod
    def complete_swap(post, user):
        """完成交換"""
        try:
            if user == post.user and post.status == 'IN_PROGRESS':
                post.status = 'PENDING_COMPLETION'
                post.confirmation_deadline = timezone.now() + timedelta(hours=24)
                post.save()
                return True, '等待交換者確認完成。'
            elif user == post.swapper and post.status == 'PENDING_COMPLETION':
                post.status = 'COMPLETED'
                post.save()
                return True, '交換已完成。'
            return False, '無法完成交換。'
        except Exception as e:
            logger.error(f"完成交換時發生錯誤: {str(e)}")
            return False, str(e)

    @staticmethod
    def cancel_swap(post, user):
        """取消交換"""
        try:
            if post.status not in ['IN_PROGRESS', 'PENDING_COMPLETION']:
                return False, '當前狀態無法取消交換。'

            if post.status == 'IN_PROGRESS':
                post.status = 'PENDING_CANCELLATION'
                post.cancellation_initiator = user
                post.confirmation_deadline = timezone.now() + timedelta(hours=24)
                post.save()
                return True, '等待對方確認取消。'

            if post.status == 'PENDING_COMPLETION' and user == post.swapper:
                post.status = 'PENDING_CANCELLATION'
                post.cancellation_initiator = user
                post.confirmation_deadline = timezone.now() + timedelta(hours=24)
                post.save()
                return True, '等待對方確認取消。'

            return False, '無法取消交換。'
        except Exception as e:
            logger.error(f"取消交換時發生錯誤: {str(e)}")
            return False, str(e)

    @staticmethod
    def confirm_cancellation(post, user):
        """確認取消"""
        try:
            if post.status != 'PENDING_CANCELLATION':
                return False, '當前狀態無法確認取消。'
            if user == post.cancellation_initiator:
                return False, '發起取消方無法確認取消。'

            post.status = 'CANCELLED'
            post.save()
            return True, '交換已取消。'
        except Exception as e:
            logger.error(f"確認取消時發生錯誤: {str(e)}")
            return False, str(e)

    @staticmethod
    def check_timeout(post):
        """檢查是否超時"""
        try:
            if post.confirmation_deadline and timezone.now() > post.confirmation_deadline:
                if post.status in ['PENDING_COMPLETION', 'PENDING_CANCELLATION']:
                    post.status = 'CANCELLED'
                    post.save()
                    return True, '由於超過確認期限，交換已自動取消。'
            return False, None
        except Exception as e:
            logger.error(f"檢查超時時發生錯誤: {str(e)}")
            return False, str(e)