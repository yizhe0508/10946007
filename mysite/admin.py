from django.contrib import admin
from .models import User, Game, Server, SwapPost

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'nickname', 'is_active', 'is_staff', 'created_at', 'updated_at')
    search_fields = ('email', 'username', 'nickname')

@admin.register(SwapPost)
class SwapPostAdmin(admin.ModelAdmin):
    list_display = ('user', 'game', 'server', 'item_name', 'item_description', 'desired_item', 'swap_time', 'swap_location', 'role_name', 'status', 'created_at', 'updated_at')
    list_filter = ('game', 'server', 'status', 'created_at', 'updated_at')
    search_fields = ('item_name', 'item_description', 'desired_item', 'role_name')
    ordering = ('-created_at',)  # 以建立時間倒序顯示

    # 如果需要在編輯頁面中顯示更詳細的字段，可以這樣配置
    fieldsets = (
        (None, {
            'fields': ('user', 'game', 'server', 'item_name', 'item_image', 'item_description', 'desired_item', 'swap_time', 'swap_location', 'role_name', 'status')
        }),
        ('Date Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),  # 讓這些字段在編輯頁面上折疊
        }),
    )

        # 允許編輯交換貼文的欄位
    def get_readonly_fields(self, request, obj=None):
        if obj:  # 編輯模式下
            return ['created_at', 'updated_at']
        return []

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
    ordering = ('name',)

@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'game')
    list_filter = ('game',)
    search_fields = ('name',)
    ordering = ('name',)
