from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


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
        user.set_password(password)
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
    password = models.CharField(max_length=128, verbose_name='password') # 可移除
    nickname = models.CharField(max_length=50, blank=True, null=True, verbose_name='暱稱')
    is_email_verified = models.BooleanField(default=False, verbose_name='信箱驗證')
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
    
class Game(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.name

class Server(models.Model):
    name = models.CharField(max_length=100)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='servers')

    class Meta:
        unique_together = ('game', 'name')  # 確保在同一個遊戲中伺服器名稱唯一

    def __str__(self):
        return f"{self.game.name} - {self.name}"

class SwapPost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    server = models.ForeignKey(Server, on_delete=models.CASCADE)
    item_name = models.CharField(max_length=200)
    item_image = models.ImageField(upload_to='items/', blank=True, null=True) 
    item_description = models.TextField()
    desired_item = models.CharField(max_length=200)
    swap_time = models.DateTimeField() 
    swap_location = models.CharField(max_length=200) 
    role_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    swapper = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='swap_requests')
    is_owner_confirmed = models.BooleanField(default=False)
    is_swapper_confirmed = models.BooleanField(default=False)
    confirmation_deadline = models.DateTimeField(null=True, blank=True)
    cancellation_initiator = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='cancellation_initiated_swaps')

    STATUS_CHOICES = [
        ('WAITING', '待交換'),
        ('IN_PROGRESS', '進行中'),
        ('PENDING_COMPLETION', '等待確認完成'),
        ('PENDING_CANCELLATION', '等待確認取消'),
        ('COMPLETED', '已完成'),
        ('CANCELLED', '已取消'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='WAITING')

    def __str__(self):
        return f"{self.item_name} - {self.user.username}"

    def can_edit(self):
        return self.status in ['WAITING', 'IN_PROGRESS']

    def can_cancel(self):
        return self.status in ['WAITING', 'IN_PROGRESS']

class SwapMessage(models.Model):
    swap_post = models.ForeignKey(SwapPost, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.sender.username}: {self.content[:50]}'