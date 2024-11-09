from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings
from django.contrib.auth.decorators import login_required
from .models import SwapPost, Game, Server, User, SwapMessage
from django.http import JsonResponse
from django.utils.dateparse import parse_datetime
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages as django_messages
from django.db.models import Q


def index(request):
    swap_posts = SwapPost.objects.filter(status='WAITING').order_by('-updated_at', '-created_at')
    
    selected_game = request.GET.get('game')
    selected_server = request.GET.get('server')
    item_name = request.GET.get('item_name', '')
    
    # 只有當用戶提交了搜索時才應用過濾器
    if 'search' in request.GET:
        query = Q(status='WAITING')  # 確保在搜索時也只包含待交換的貼文
        if selected_game:
            query &= Q(game_id=int(selected_game))
        if selected_server:
            query &= Q(server_id=int(selected_server))
        if item_name:
            query &= Q(item_name__icontains=item_name)

        swap_posts = swap_posts.filter(query)
    print(f"Selected server: {request.GET.get('server')}")


    games = Game.objects.all()
    servers = []  # 初始化為空列表

    if selected_game:
        servers = Server.objects.filter(game_id=selected_game)

    # 每頁顯示 5 個貼文
    paginator = Paginator(swap_posts, 5)
    
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'games': games,
        'servers': servers,
        'swap_posts': page_obj,
        'selected_game': selected_game,
        'selected_server': selected_server,
        'item_name': item_name,
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
            messages.error(request, '請輸入您的帳號', extra_tags='register_message')
            return render(request, 'register.html')

        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, '請輸入有效的信箱地址!', extra_tags='register_message')
            return render(request, 'register.html')

        if not password1 or not password2:
            messages.error(request, '請輸入您的密碼', extra_tags='register_message')
            return render(request, 'register.html')

        if password1 != password2:
            messages.error(request, '您輸入的密碼不一致', extra_tags='register_message')
            return render(request, 'register.html')

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
            messages.error(request, '該帳號已經存在!', extra_tags='register_message')
            return render(request, 'register.html')

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

        # 確保帳號或信箱與密碼非空值
        if not username_or_email or not password:
            messages.error(request, '請填寫帳號或信箱及密碼。', extra_tags='login_message')
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
                messages.error(request, '帳號尚未啟用，請檢查您的郵件並進行驗證。', extra_tags='login_message')
        else:
            messages.error(request, '無效的帳號或密碼，請重新輸入。', extra_tags='login_message')

    return render(request, 'login.html')

def logout_view(request):
    logout(request)  # 執行登出操作
    return redirect('index')  # 登出後重定向到首頁

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            
            # 設置重設期限
            reset_days = getattr(settings, 'PASSWORD_RESET_TIMEOUT_DAYS', 1)  # 默認 1 天
            
            # 發送重設密碼郵件
            current_site = get_current_site(request)
            mail_subject = '【虛擬寶物交換網】請重設您的密碼'
            
            # HTML message
            message_html = render_to_string('reset_password_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
                'reset_days': reset_days,
            })

            message_plain = render_to_string('reset_password_email.txt', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
                'reset_days': reset_days,
            })            

            email_message = EmailMultiAlternatives(
                subject=mail_subject,
                body=message_plain,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email],
            )
            email_message.attach_alternative(message_html, "text/html")
            email_message.send(fail_silently=False)
            
            messages.success(request, '重設密碼的郵件已發送，請查看您的信箱。')
            return redirect('login')
        except User.DoesNotExist:
            messages.error(request, '該信箱地址不存在。')
    return render(request, 'forgot_password.html')

def reset_password_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            if new_password == confirm_password:
                user.set_password(new_password)
                user.save()
                messages.success(request, '密碼已成功重設，請使用新密碼登入。')
                return redirect('login')
            else:
                messages.error(request, '兩次輸入的密碼不一致。')
        return render(request, 'reset_password_confirm.html')
    else:
        messages.error(request, '密碼重設連結無效或已過期。')
        return redirect('login')

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

@login_required
def swap_manage(request):
    post_type = request.GET.get('type', 'my_posts')  # 默認顯示使用者自己的貼文
    
    if post_type == 'participated_posts':
        all_posts = SwapPost.objects.filter(swapper=request.user).order_by('-updated_at', '-created_at')
    else:
        all_posts = SwapPost.objects.filter(user=request.user).order_by('-updated_at', '-created_at')
    
    paginator = Paginator(all_posts, 5)  # 每頁顯示 5 個貼文
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'swap_posts': page_obj,
        'post_type': post_type,
    }
    
    return render(request, 'swap_manage.html', context)

@login_required
def update_swap_status(request, post_id):
    post = get_object_or_404(SwapPost, id=post_id, user=request.user)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(SwapPost.STATUS_CHOICES).keys():
            post.status = new_status
            post.save()
            messages.success(request, '交換狀態已更新。')
        else:
            messages.error(request, '無效的狀態。')
    return redirect('swap_manage')

@login_required
@require_POST
def delete_swap_post(request, post_id):
    if not post.can_cancel(request.user):
        return JsonResponse({'success': False, 'error': '您沒有權限刪除此貼文。'})

    try:
        post = SwapPost.objects.get(id=post_id, user=request.user)
        post.delete()
        return JsonResponse({'success': True})
    except SwapPost.DoesNotExist:
        return JsonResponse({'success': False, 'error': '貼文不存在或您沒有權限刪除'})

@login_required
def edit_swap_post(request, post_id):
    post = get_object_or_404(SwapPost, id=post_id, user=request.user)
    
    if not post.can_edit(request.user):
        messages.error(request, '您沒有權限編輯此貼文。')
        return redirect('swap_manage')

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

        # 确保所有必要的字段都有值
        if not game_id or not server_id or not item_name or not item_description or not desired_item or not swap_time or not swap_location or not role_name:
            messages.error(request, '所有欄位都是必填的！')
            return render(request, 'edit_swap_post.html', {'post': post, 'games': Game.objects.all(), 'servers': Server.objects.filter(game_id=game_id)})

        try:
            game = Game.objects.get(id=game_id)
            server = Server.objects.get(id=server_id, game=game)  # 確保伺服器和遊戲對應
        except Game.DoesNotExist:
            messages.error(request, '選擇的遊戲不存在。')
            return redirect('edit_swap_post', post_id=post_id)
        except Server.DoesNotExist:
            messages.error(request, '選擇的伺服器不存在。')
            return redirect('edit_swap_post', post_id=post_id)

        # 將 swap_time 轉換為 datetime 對象
        swap_time = parse_datetime(swap_time)
        
        # 圖片處理
        if item_img:
            img = Image.open(item_img)
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            output = BytesIO()
            img.save(output, format='JPEG', quality=85)
            item_img = InMemoryUploadedFile(
                output, 'ImageField', f'{item_name}.jpg', 'image/jpeg', output.tell(), None
            )

        # 更新交換貼文
        try:
            post.game = game
            post.server = server
            post.item_name = item_name
            if item_img:
                post.item_image = item_img
            post.item_description = item_description
            post.desired_item = desired_item
            post.swap_time = swap_time
            post.swap_location = swap_location
            post.role_name = role_name
            post.save()
            messages.success(request, '交換貼文已成功更新！')
            return redirect('swap_manage')
        except Exception as e:
            messages.error(request, f'發生錯誤: {e}')

    else:
        context = {
            'post': post,
            'games': Game.objects.all(),
            'servers': Server.objects.filter(game=post.game)
        }
        return render(request, 'edit_swap_post.html', context)

@require_POST
def update_post_time(request, post_id):
    post = get_object_or_404(SwapPost, id=post_id)
    post.updated_at = timezone.now()  # 更新為當前時間
    post.save()
    # 確保轉換為台北時區並格式化
    formatted_time = timezone.localtime(post.updated_at).strftime("%Y/%m/%d %H:%M")
    return JsonResponse({
        'success': True,
        'updated_at': formatted_time  # 回傳格式化的時間
    })

@login_required
def active_swap(request, post_id):
    post = get_object_or_404(SwapPost, id=post_id)

    # 檢查是否是從等待狀態進入    
    if post.status == 'WAITING' and request.user != post.user:
        post.status = 'IN_PROGRESS'
        post.swapper = request.user
        post.save()
        messages.success(request, '您已成功加入交换!')    

    # 確保只有有效的使用者可以訪問
    if request.user != post.user and request.user != post.swapper:
        django_messages.error(request, '您沒有權限訪問此頁面。')
        return redirect('index')

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'complete':
            if post.status == 'IN_PROGRESS' and request.user == post.user:
                post.status = 'PENDING_COMPLETION'
                post.confirmation_deadline = timezone.now() + timedelta(hours=24)
                post.save()
                django_messages.success(request, '等待交換者確認完成。')
            elif post.status == 'PENDING_COMPLETION' and request.user == post.swapper:
                post.status = 'COMPLETED'
                post.save()
                django_messages.success(request, '交換已完成。')
                return redirect('index')
        
    # 處理 POST 請求
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'complete':
            if post.status == 'IN_PROGRESS' and request.user == post.user:
                post.status = 'PENDING_COMPLETION'
                post.confirmation_deadline = timezone.now() + timedelta(hours=24)
                post.save()
                messages.success(request, '等待交換者確認完成。')
            elif post.status == 'PENDING_COMPLETION' and request.user == post.swapper:
                post.status = 'COMPLETED'
                post.save()
                messages.success(request, '交換已完成。')
                return redirect('index')
        
        elif action == 'cancel':
            if post.status == 'IN_PROGRESS':
                post.status = 'PENDING_CANCELLATION'
                post.cancellation_initiator = request.user
                post.confirmation_deadline = timezone.now() + timedelta(hours=24)
                post.save()
                messages.success(request, '等待對方確認取消。')
                
            elif post.status == 'PENDING_COMPLETION':
                # 如果貼文者已完成交換，參與者發起取消請求
                if request.user == post.swapper:
                    post.status = 'PENDING_CANCELLATION'
                    post.cancellation_initiator = request.user
                    post.confirmation_deadline = timezone.now() + timedelta(hours=24)
                    post.save()
                    messages.success(request, '等待對方確認取消，因為交換者已發起取消請求。')
                else:
                    messages.error(request, '交換已進入完成階段，無法取消。')
            
            elif post.status == 'PENDING_CANCELLATION':
                # 檢查是否是非發起者在確認取消
                if request.user != post.cancellation_initiator:
                    post.status = 'CANCELLED'
                    post.save()
                    messages.success(request, '交換已取消。')
                    return redirect('index')
                else:
                    messages.error(request, '您已發起取消請求，等待對方確認。')
        
        return redirect('active_swap', post_id=post_id)
    
    # 處理超時
    if post.confirmation_deadline and timezone.now() > post.confirmation_deadline:
        if post.status in ['PENDING_COMPLETION', 'PENDING_CANCELLATION']:
            post.status = 'CANCELLED'
            post.save()
            django_messages.warning(request, '由於超過確認期限，交換已自動取消。')
    
    swap_messages = post.messages.all()
    context = {
        'post': post,
        'swap_messages': swap_messages,
        'is_cancellation_initiator': post.status == 'PENDING_CANCELLATION' and request.user == post.cancellation_initiator,
        'can_confirm_cancellation': post.status == 'PENDING_CANCELLATION' and request.user != post.cancellation_initiator,
    }
    return render(request, 'active_swap.html', context)

@login_required
@require_POST
def send_message(request, post_id):
    post = get_object_or_404(SwapPost, id=post_id)
    content = request.POST.get('content')
    if content:
        message = SwapMessage.objects.create(
            swap_post=post,
            sender=request.user,
            content=content
        )
        return JsonResponse({
            'status': 'success',
            'message': {
                'id': message.id,
                'sender': message.sender.username,
                'content': message.content,
                'created_at': message.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    return JsonResponse({'status': 'error', 'message': 'Content is required'})

@login_required
def get_messages(request, post_id):
    post = get_object_or_404(SwapPost, id=post_id)
    last_message_id = request.GET.get('last_id')
    messages = post.messages.filter(id__gt=last_message_id) if last_message_id else post.messages.all()
    return JsonResponse({
        'messages': [{
            'id': message.id,
            'sender': message.sender.username,
            'content': message.content,
            'created_at': message.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for message in messages]
    })

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
                messages.error(request, '請輸入有效的信箱地址！', extra_tags='account_message')
                return render(request, 'account.html')

        # 僅在密碼實際改變時添加成功消息
        if current_password and new_password and confirm_new_password:
            if not user.check_password(current_password):
                messages.error(request, '目前密碼不正確！', extra_tags='account_message')
                return render(request, 'account.html')
            if new_password != confirm_new_password:
                messages.error(request, '新密碼不一致！', extra_tags='account_message')
                return render(request, 'account.html')
            user.set_password(new_password)
            update_session_auth_hash(request, user)  # 更新 session 以防登出
            success_messages.append('密碼已成功變更！')

        user.save()

        for message in success_messages:
            messages.success(request, message, extra_tags='account_message')

        return redirect('account')  # 假設 'account' 是顯示帳號資料的頁面

    return render(request, 'account.html')

def error_404(request, exception):
    return render(request, '404.html', status=404)