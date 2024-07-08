from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth import get_user_model
import uuid


class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None):
        if not email:
            raise ValueError('必須有電子郵件地址')
        if not username:
            raise ValueError('必須有使用者名稱')

        user = self.model(
            email=self.normalize_email(email),
            username=username,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None):
        user = self.create_user(
            email,
            username=username,
            password=password,
        )
        user.is_email_verified = True
        user.is_superuser = True
        user.is_staff = True
        user.is_active = True
        user.save(using=self._db)
        return user
    
class User(AbstractBaseUser, PermissionsMixin):
    user_id = models.AutoField(primary_key=True, verbose_name='ID')
    username = models.CharField(max_length=50, unique=True, verbose_name='使用者名稱')
    email = models.EmailField(verbose_name='信箱', max_length=255, unique=True)
    password = models.CharField(max_length=128, verbose_name='password')
    nickname = models.CharField(max_length=50, blank=True, null=True, verbose_name='暱稱')
    is_email_verified = models.BooleanField(default=False, verbose_name='信箱已驗證')
    is_active = models.BooleanField(default=True, verbose_name='啟用')
    is_staff = models.BooleanField(default=False)  # 用來控制用戶是否可以登入 Django 的管理界面
    is_superuser = models.BooleanField(default=False)  # 用來控制用戶是否具有超級用戶權限
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='建立時間')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新時間')

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_active and (self.is_superuser or self.is_staff)

    def has_module_perms(self, app_label):
        return self.is_active and (self.is_superuser or self.is_staff)
