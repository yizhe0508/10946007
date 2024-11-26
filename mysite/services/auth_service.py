# services/auth_service.py
from asyncio.log import logger
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

class AuthService:
    @staticmethod
    def validate_registration_data(username, email, password1, password2):
        if not username:
            raise ValidationError('請輸入您的帳號')
            
        validate_email(email)
            
        if not password1 or not password2:
            raise ValidationError('請輸入您的密碼')
            
        if password1 != password2:
            raise ValidationError('您輸入的密碼不一致')

    @staticmethod
    def create_inactive_user(username, email, password):
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        user.is_active = False
        user.save()
        return user

    @staticmethod
    def activate_user(user):
        user.is_email_verified = True
        user.is_active = True
        user.save()

    @staticmethod
    def authenticate_user(username_or_email, password):
        if not username_or_email or not password:
            return None, '請填寫帳號或信箱及密碼。'
        
        try:
            user = authenticate(username_or_email=username_or_email, password=password)
            if not user:
                return None, '無效的帳號或密碼，請重新輸入。'
            if not user.is_active:
                return None, '帳號尚未啟用，請檢查您的郵件並進行驗證。'
            return user, None
            
        except Exception as e:
            logger.error(f"登入驗證發生錯誤: {str(e)}")
            return None, '無效的帳號或密碼，請重新輸入。'