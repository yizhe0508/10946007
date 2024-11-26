# services/profile_service.py
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)

class ProfileService:
    @staticmethod
    def update_nickname(user, nickname):
        if not nickname or nickname == user.nickname:
            return False, None
        
        try:
            user.nickname = nickname
            return True, '暱稱已成功變更！'
        except Exception as e:
            logger.error(f"更新暱稱時發生錯誤: {str(e)}")
            return False, '更新暱稱時發生錯誤'

    @staticmethod
    def update_email(user, email):
        if not email or email == user.email:
            return False, None
            
        try:
            validate_email(email)
            user.email = email
            user.is_email_verified = False
            return True, '請檢查您的新信箱進行驗證！'
        except ValidationError:
            return False, '請輸入有效的信箱地址！'
        except Exception as e:
            logger.error(f"更新信箱時發生錯誤: {str(e)}")
            return False, '更新信箱時發生錯誤'

    @staticmethod
    def update_password(user, current_password, new_password, confirm_password):
        if not all([current_password, new_password, confirm_password]):
            return False, None
            
        if not user.check_password(current_password):
            return False, '目前密碼不正確！'
            
        if new_password != confirm_password:
            return False, '新密碼不一致！'
            
        try:
            user.set_password(new_password)
            return True, '密碼已成功變更！'
        except Exception as e:
            logger.error(f"更新密碼時發生錯誤: {str(e)}")
            return False, '更新密碼時發生錯誤'