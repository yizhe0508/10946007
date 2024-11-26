# services/password_service.py
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator
import logging

logger = logging.getLogger(__name__)

class PasswordService:
    @staticmethod
    def validate_reset_token(uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            if user and default_token_generator.check_token(user, token):
                return user, None
        except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
            logger.error(f"驗證重設密碼token時發生錯誤: {str(e)}")
        return None, '密碼重設連結無效或已過期。'

    @staticmethod
    def reset_password(user, new_password, confirm_password):
        if new_password != confirm_password:
            return False, '兩次輸入的密碼不一致。'
        
        try:
            user.set_password(new_password)
            user.save()
            return True, '密碼已成功重設，請使用新密碼登入。'
        except Exception as e:
            logger.error(f"重設密碼時發生錯誤: {str(e)}")
            return False, '重設密碼時發生錯誤，請稍後再試。'