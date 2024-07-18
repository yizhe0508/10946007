from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from venv import logger
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings
from django.contrib.auth.decorators import login_required
from .models import SwapPost, Game, Server, User
from django.http import JsonResponse
from django.utils.dateparse import parse_datetime
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.paginator import Paginator

def index(request):
    swap_posts = SwapPost.objects.all().order_by('-created_at')
    
    # 每頁顯示 10 個貼文，你可以根據需要調整這個數字
    paginator = Paginator(swap_posts, 5)
    
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'swap_posts': page_obj,
    }
    
    if request.user.is_authenticated:
        context['user'] = request.user
    
    return render(request, 'index.html', context)

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

@login_required
def add_swap_post(request):
    if request.method == 'POST':
        game_id = request.POST.get('game')
        server_id = request.POST.get('server')
        item_name = request.POST.get('itemName')
        item_img = request.FILES.get('itemImg')
        item_description = request.POST.get('itemDescribe')
        desired_item = request.POST.get('desired_item')
        swap_time = request.POST.get('swapTime')
        swap_location = request.POST.get('swapLocation')
        role_name = request.POST.get('roleName')
        status = 'WAITING'  # 預設狀態

        # 確保所有必要的字段都有值
        if not game_id or not server_id or not item_name or not item_description or not desired_item or not swap_time or not swap_location or not role_name:
            messages.error(request, '所有欄位都是必填的！')
            return render(request, 'add_swap_post.html', {'games': Game.objects.all(), 'servers': Server.objects.filter(game_id=game_id)})

        try:
            game = Game.objects.get(id=game_id)
            server = Server.objects.get(id=server_id, game=game)  # 確保伺服器和遊戲對應
        except Game.DoesNotExist:
            messages.error(request, '選擇的遊戲不存在。')
            return redirect('add_swap_post')
        except Server.DoesNotExist:
            messages.error(request, '選擇的伺服器不存在。')
            return redirect('add_swap_post')

        # 將 swap_time 轉換為 datetime 對象
        swap_time = parse_datetime(swap_time)
        
        # 圖片處理
        if item_img:
            img = Image.open(item_img)

            # 如果圖片是 RGBA 模式，將其轉換為 RGB 模式
            if img.mode == 'RGBA':
                img = img.convert('RGB')

            # 保持原始尺寸進行壓縮
            output = BytesIO()
            img.save(output, format='JPEG', quality=85)
            item_img = InMemoryUploadedFile(
                output, 'ImageField', f'{item_name}.jpg', 'image/jpeg', output.tell(), None
            )

        # 創建新的交換貼文
        try:
            SwapPost.objects.create(
                user=request.user,
                game=game,
                server=server,
                item_name=item_name,
                item_image=item_img,
                item_description=item_description,
                desired_item=desired_item,
                swap_time=swap_time,
                swap_location=swap_location,
                role_name=role_name,
                status=status
            )
            messages.success(request, '交換貼文已成功新增！')
            return redirect('index')  # 根據需要重定向到你的首頁或其他頁面
        except Exception as e:
            messages.error(request, f'發生錯誤: {e}')

    else:
        game_id = request.GET.get('game_id')
        servers = Server.objects.filter(game_id=game_id) if game_id else Server.objects.none()
        return render(request, 'add_swap_post.html', {'games': Game.objects.all(), 'servers': servers})
    
def get_servers(request):
    game_id = request.GET.get('game_id')
    servers = Server.objects.filter(game_id=game_id).values('id', 'name')
    return JsonResponse({'servers': list(servers)}) 

def swap_manage(request):
    return render(request, 'swap_manage.html')

def edit_swap_post(request):
    if request.method == 'POST':
        item_image = request.FILES['item-image']
        # 這裡處理你的文件上傳邏輯
    return render(request, 'edit_swap_post.html')

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
    return render(request, '404.html', status=404)