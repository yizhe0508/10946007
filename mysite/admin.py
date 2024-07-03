from django.contrib import admin
from .models import User  # 假設您的模型類名為User

class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'nickname', 'created_at', 'updated_at', 'is_active')

admin.site.register(User, UserAdmin)