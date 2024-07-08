from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from venv import logger
from django.contrib import messages
from .models import User
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings
from django.contrib.auth.decorators import login_required


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

            # 設置驗證期限
            activation_days = getattr(settings, 'ACCOUNT_ACTIVATION_DAYS', 7)  # 默認 7 天

            # 發送驗證郵件
            current_site = get_current_site(request)
            mail_subject = '請啟用您的【虛擬寶物交換網】帳號'

            # HTML message
            message_html = render_to_string('activation_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
                'activation_days': activation_days,  # 傳遞驗證期限到模板
            })

            message_plain = render_to_string('activation_email.txt', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
                'activation_days': activation_days,  # 傳遞驗證期限到模板
            })            

            to_email = email
            email_message = EmailMultiAlternatives(
                subject=mail_subject,
                body=message_plain,  # Text version of the email
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[to_email],
            )
            email_message.attach_alternative(message_html, "text/html")  # HTML version

            email_message.send(fail_silently=False)      
        
            return redirect('register_success')
        except IntegrityError:
            error = '該帳號已經存在'
            logger.error('IntegrityError: %s', error)
            return render(request, 'register.html', {'error': error})

    return render(request, 'register.html')

def register_success(request):
    return render(request, 'register_success.html')

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_email_verified = True 
        user.is_active = True
        user.save()
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')  # 添加 backend 參數
        return redirect('activation_success')
    else:
        return redirect('activation_invalid')

def activate_success(request):
    return render(request, 'activation_success.html')

def activate_invalid(request): 
    return render(request, 'activation_invalid.html')

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

def logout_view(request):
    logout(request)  # 執行登出操作
    return redirect('index')  # 登出後重定向到首頁

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

@login_required
def update_profile(request):
    if request.method == 'POST':
        nickname = request.POST.get('nickname')
        email = request.POST.get('email')
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_new_password = request.POST.get('confirm_new_password')

        user = request.user
        success_messages = []

        # 僅在暱稱實際改變時添加成功消息
        if nickname and nickname != user.nickname:
            user.nickname = nickname
            success_messages.append('暱稱已成功變更！')

        # 僅在信箱實際改變時添加成功消息
        if email and email != user.email:
            try:
                validate_email(email)
                user.email = email
                user.is_email_verified = False  # 更改信箱後需要重新驗證
                user.save()

                # 設置驗證期限
                activation_days = getattr(settings, 'ACCOUNT_ACTIVATION_DAYS', 7)  # 默認 7 天
                
                # 發送驗證郵件
                current_site = get_current_site(request)
                mail_subject = '【虛擬寶物交換網】請確認您的新信箱地址'
                
                # HTML message
                message_html = render_to_string('activation_email.html', {
                    'user': user,
                    'domain': current_site.domain,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': default_token_generator.make_token(user),
                    'activation_days': activation_days,  # 傳遞驗證期限到模板
                })

                message_plain = render_to_string('activation_email.txt', {
                    'user': user,
                    'domain': current_site.domain,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': default_token_generator.make_token(user),
                    'activation_days': activation_days,  # 傳遞驗證期限到模板
                })      

                to_email = email
                email_message = EmailMultiAlternatives(
                    subject=mail_subject,
                    body=message_plain,  # Text version of the email
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[to_email],
                )
                email_message.attach_alternative(message_html, "text/html")  # HTML version
                email_message.send(fail_silently=False)

                success_messages.append('請檢查您的新信箱進行驗證！')

            except ValidationError:
                messages.error(request, '請輸入有效的信箱地址！')
                return render(request, 'account.html')

        # 僅在密碼實際改變時添加成功消息
        if current_password and new_password and confirm_new_password:
            if not user.check_password(current_password):
                messages.error(request, '目前密碼不正確！')
                return render(request, 'account.html')
            if new_password != confirm_new_password:
                messages.error(request, '新密碼不一致！')
                return render(request, 'account.html')
            user.set_password(new_password)
            update_session_auth_hash(request, user)  # 更新 session 以防登出
            success_messages.append('密碼已成功變更！')

        user.save()

        for message in success_messages:
            messages.success(request, message)

        return redirect('account')  # 假設 'account' 是顯示帳號資料的頁面

    return render(request, 'account.html')

def error_404(request, exception):
    return render(request, 'error_404.html')