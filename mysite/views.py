from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from venv import logger
from django.contrib import messages
from .models import User

def index(request):
    # 檢查用戶是否已登入
    if request.user.is_authenticated:
        # 用戶已登入，可以將用戶信息傳遞給模板
        return render(request, 'index.html', {'user': request.user})
    else:
        # 用戶未登入，可選擇重定向到登入頁面或僅顯示一般首頁
        return render(request, 'index.html')

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        # 後端驗證
        if not username:
            error = '請輸入您的帳號'
            return render(request, 'register.html', {'error': error})

        try:
            validate_email(email)
        except ValidationError:
            error = '請輸入有效的信箱地址'
            return render(request, 'register.html', {'error': error})

        if not password1 or not password2:
            error = '請輸入您的密碼'
            return render(request, 'register.html', {'error': error})

        if password1 != password2:
            error = '您輸入的密碼不一致'
            return render(request, 'register.html', {'error': error})

        try:
            user = User.objects.create_user(username=username, email=email, password=password1)
            user.is_active = False  # 用戶需要通過郵件驗證後才啟用
            user.save()
            # 發送郵件驗證的邏輯
            return redirect('login')
        except IntegrityError:
            error = '該帳號已經存在'
            logger.error('IntegrityError: %s', error)
            return render(request, 'register.html', {'error': error})

    return render(request, 'register.html')

def login_view(request):
    if request.method == 'POST':
        username_or_email = request.POST.get('username_or_email')
        password = request.POST.get('password')

        if not username_or_email:
            messages.error(request, 'Username or Email must be filled out')
            return render(request, 'login.html')

        if not password:
            messages.error(request, 'Password must be filled out')
            return render(request, 'login.html')

        # 嘗試用使用者名稱或電子郵件登入
        try:
            user = authenticate(request, username_or_email=username_or_email, password=password)
        except ValidationError:
            user = None

        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect('index')  # 根據需要重定向到你的首頁或其他頁面
            else:
                messages.error(request, '帳號尚未啟用，請檢查您的郵件進行驗證。')
        else:
            messages.error(request, '無效的帳號或密碼，請重新輸入。')

    return render(request, 'login.html')

def add_swap(request):
    if request.method == 'POST':
        item_image = request.FILES['item-image']
        # 這裡處理你的文件上傳邏輯
    return render(request, 'add_swap.html')

def swap_manage(request):
    return render(request, 'swap_manage.html')

def edit_swap(request):
    if request.method == 'POST':
        item_image = request.FILES['item-image']
        # 這裡處理你的文件上傳邏輯
    return render(request, 'edit_swap.html')

def active_swap(request):
    return render(request, 'active_swap.html')

def account(request):
    return render(request, 'account.html')

def error_404(request, exception):
    return render(request, 'error_404.html')