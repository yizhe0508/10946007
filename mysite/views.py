from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .services.swap_post_service import SwapPostService
from .models import SwapPost, Game, Server, User
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .services.search_service import SwapPostSearchService
from .services.pagination_service import PaginationService
from .services.game_server_service import GameService
from .services.auth_service import AuthService
from .services.email_service import EmailService
from .services.password_service import PasswordService
from .services.profile_service import ProfileService
from .services.swap_progress_service import SwapProgressService
from .services.message_service import MessageService

def index(request):
    # 初始化服務
    search_service = SwapPostSearchService()
    pagination_service = PaginationService()
    game_service = GameService()
    
    # 獲取搜尋參數
    search_filters = {
        'game_id': request.GET.get('game'),
        'server_id': request.GET.get('server'),
        'item_name': request.GET.get('item_name', '')
    }
    
    # 執行搜尋
    if 'search' in request.GET:
        swap_posts = search_service.search_posts(search_filters)
    else:
        swap_posts = search_service.search_posts()
    
    # 分頁處理
    page_obj = pagination_service.paginate_queryset(
        swap_posts,
        request.GET.get('page')
    )
    
    # 獲取遊戲和伺服器資料
    games = game_service.get_all_games()
    servers = game_service.get_servers_for_game(search_filters['game_id'])
    
    # 準備模板上下文
    context = {
        'games': games,
        'servers': servers,
        'swap_posts': page_obj,
        'selected_game': search_filters['game_id'],
        'selected_server': search_filters['server_id'],
        'item_name': search_filters['item_name'],
    }
    
    if request.user.is_authenticated:
        context['user'] = request.user
    
    return render(request, 'index.html', context)

def register(request):
    if request.method == 'POST':
        try:
            auth_service = AuthService()
            auth_service.validate_registration_data(
                request.POST['username'],
                request.POST['email'],
                request.POST['password1'],
                request.POST['password2']
            )
            
            user = auth_service.create_inactive_user(
                request.POST['username'],
                request.POST['email'],
                request.POST['password1']
            )
            
            EmailService.send_activation_email(request, user)
            return redirect('register_success')
            
        except ValidationError as e:
            messages.error(request, str(e), extra_tags='register_message')
        except Exception:
            messages.error(request, '註冊過程發生錯誤', extra_tags='register_message')
    
    return render(request, 'register.html')

def register_success(request):
    return render(request, 'register_success.html')

def activate(request, uidb64, token):
    user = PasswordService.validate_reset_token(uidb64, token)
    if user:
        AuthService.activate_user(user)
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return redirect('activation_success')
    return redirect('activation_invalid')

def activate_success(request):
    return render(request, 'activation_success.html')

def activate_invalid(request): 
    return render(request, 'activation_invalid.html')

def login_view(request):
    if request.method == 'POST':
        username_or_email = request.POST.get('username_or_email')
        password = request.POST.get('password')
        
        user, error_message = AuthService.authenticate_user(username_or_email, password)
        
        if user:
            login(request, user)
            return redirect('index')
        else:
            messages.error(request, error_message, extra_tags='login_message')
    
    return render(request, 'login.html')

def logout_view(request):
    logout(request)  # 執行登出操作
    return redirect('index')  # 登出後重定向到首頁

def forgot_password(request):
    if request.method == 'POST':
        try:
            user = User.objects.get(email=request.POST.get('email'))
            EmailService.send_password_reset_email(request, user)
            messages.success(request, '重設密碼的郵件已發送，請查看您的信箱。')
            return redirect('login')
        except User.DoesNotExist:
            messages.error(request, '該信箱地址不存在。')
    
    return render(request, 'forgot_password.html')

def reset_password_confirm(request, uidb64, token):
    user = PasswordService.validate_reset_token(uidb64, token)
    if not user:
        messages.error(request, '密碼重設連結無效或已過期。')
        return redirect('login')
        
    if request.method == 'POST':
        try:
            PasswordService.reset_password(
                user,
                request.POST.get('new_password'),
                request.POST.get('confirm_password')
            )
            messages.success(request, '密碼已成功重設，請使用新密碼登入。')
            return redirect('login')
        except ValidationError as e:
            messages.error(request, str(e))
    
    return render(request, 'reset_password_confirm.html')

@login_required
def update_profile(request):
    if request.method == 'POST':
        user = request.user
        success_messages = []
        profile_service = ProfileService()
        
        # 更新暱稱
        success, message = profile_service.update_nickname(
            user, 
            request.POST.get('nickname')
        )
        if message:
            if success:
                success_messages.append(message)
            else:
                messages.error(request, message, extra_tags='account_message')
                return render(request, 'account.html')

        # 更新信箱
        success, message = profile_service.update_email(
            user, 
            request.POST.get('email')
        )
        if message:
            if success:
                # 發送驗證郵件
                email_success, email_message = EmailService.send_activation_email(request, user)
                if not email_success:
                    messages.error(request, email_message, extra_tags='account_message')
                    return render(request, 'account.html')
                success_messages.append(message)
            else:
                messages.error(request, message, extra_tags='account_message')
                return render(request, 'account.html')

        # 更新密碼
        success, message = profile_service.update_password(
            user,
            request.POST.get('current_password'),
            request.POST.get('new_password'),
            request.POST.get('confirm_new_password')
        )
        if message:
            if success:
                update_session_auth_hash(request, user)  # 更新 session
                success_messages.append(message)
            else:
                messages.error(request, message, extra_tags='account_message')
                return render(request, 'account.html')

        user.save()

        for message in success_messages:
            messages.success(request, message, extra_tags='account_message')

        return redirect('account')

    return render(request, 'account.html')

@login_required
def add_swap_post(request):
    if request.method == 'POST':
        post_data = {
            'game_id': request.POST.get('game'),
            'server_id': request.POST.get('server'),
            'item_name': request.POST.get('itemName'),
            'item_description': request.POST.get('itemDescribe'),
            'desired_item': request.POST.get('desired_item'),
            'swap_time': request.POST.get('swapTime'),
            'swap_location': request.POST.get('swapLocation'),
            'role_name': request.POST.get('roleName'),
        }
        
        swap_service = SwapPostService()
        
        # 驗證數據
        is_valid, error_message = swap_service.validate_post_data(post_data)
        if not is_valid:
            messages.error(request, error_message)
            return render(request, 'add_swap_post.html', {
                'games': Game.objects.all(), 
                'servers': Server.objects.filter(game_id=post_data['game_id'])
            })
        
        # 創建貼文
        success, message = swap_service.create_swap_post(
            request.user, 
            post_data,
            request.FILES.get('itemImg')
        )
        
        if success:
            messages.success(request, message)
            return redirect('index')
        else:
            messages.error(request, message)
            
    # GET 請求處理
    game_id = request.GET.get('game_id')
    servers = Server.objects.filter(game_id=game_id) if game_id else Server.objects.none()
    
    return render(request, 'add_swap_post.html', {
        'games': Game.objects.all(), 
        'servers': servers
    })

def get_servers(request):
    game_id = request.GET.get('game_id')
    servers = Server.objects.filter(game_id=game_id).values('id', 'name')
    return JsonResponse({'servers': list(servers)}) 

@login_required
def swap_manage(request):
    swap_service = SwapPostService()
    post_type = request.GET.get('type', 'my_posts')
    
    page_obj, error = swap_service.get_managed_posts(
        user=request.user,
        post_type=post_type,
        page_number=request.GET.get('page')
    )
    
    if error:
        messages.error(request, error)
        
    context = {
        'swap_posts': page_obj,
        'post_type': post_type,
    }
    return render(request, 'swap_manage.html', context)

@require_POST
def update_post_time(request, post_id):
    post = get_object_or_404(SwapPost, id=post_id)
    swap_service = SwapPostService()
    
    success, result = swap_service.update_post_time(post)
    
    return JsonResponse({
        'success': success,
        'updated_at': result if success else None,
        'error': result if not success else None
    })

@login_required
def update_swap_status(request, post_id):
    post = get_object_or_404(SwapPost, id=post_id, user=request.user)
    swap_service = SwapPostService()
    
    if request.method == 'POST':
        success, message = swap_service.update_status(
            post,
            request.POST.get('status'),
            request.user
        )
        
        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)
            
    return redirect('swap_manage')

@login_required
@require_POST
def delete_swap_post(request, post_id):
    post = get_object_or_404(SwapPost, id=post_id, user=request.user)
    swap_service = SwapPostService()
    
    success, message = swap_service.delete_swap_post(post, request.user)
    return JsonResponse({'success': success, 'error': message if not success else None})

@login_required
def edit_swap_post(request, post_id):
    post = get_object_or_404(SwapPost, id=post_id, user=request.user)
    swap_service = SwapPostService()

    if not post.can_edit(request.user):
        messages.error(request, '您沒有權限編輯此貼文。')
        return redirect('swap_manage')

    if request.method == 'POST':
        post_data = {
            'game_id': request.POST.get('game'),
            'server_id': request.POST.get('server'),
            'item_name': request.POST.get('itemName'),
            'item_description': request.POST.get('itemDescribe'),
            'desired_item': request.POST.get('desired_item'),
            'swap_time': request.POST.get('swapTime'),
            'swap_location': request.POST.get('swapLocation'),
            'role_name': request.POST.get('roleName'),
        }

        success, message = swap_service.update_swap_post(
            post,
            post_data,
            request.FILES.get('itemImg')
        )

        if success:
            messages.success(request, message)
            return redirect('swap_manage')
        messages.error(request, message)

    context = {
        'post': post,
        'games': Game.objects.all(),
        'servers': Server.objects.filter(game=post.game)
    }
    return render(request, 'edit_swap_post.html', context)

@login_required
def active_swap(request, post_id):
    post = get_object_or_404(SwapPost, id=post_id)
    swap_progress_service = SwapProgressService()
    
    # 檢查超時
    is_timeout, timeout_message = swap_progress_service.check_timeout(post)
    if is_timeout:
        messages.warning(request, timeout_message)

    # 處理加入交換
    if post.status == 'WAITING' and request.user != post.user:
        success, message = swap_progress_service.join_swap(post, request.user)
        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)

    # 確保只有相關使用者可以訪問
    if request.user != post.user and request.user != post.swapper:
        messages.error(request, '您沒有權限訪問此頁面。')
        return redirect('index')

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'complete':
            success, message = swap_progress_service.complete_swap(post, request.user)
        elif action == 'cancel':
            if post.status == 'PENDING_CANCELLATION' and request.user != post.cancellation_initiator:
                success, message = swap_progress_service.confirm_cancellation(post, request.user)
            else:
                success, message = swap_progress_service.cancel_swap(post, request.user)

        if success:
            messages.success(request, message)
            if post.status in ['COMPLETED', 'CANCELLED']:
                return redirect('index')
        else:
            messages.error(request, message)
    
    swap_messages = post.messages.all()
    context = {
        'post': post,
        'swap_messages': swap_messages,
        'is_cancellation_initiator': post.status == 'PENDING_CANCELLATION' 
            and request.user == post.cancellation_initiator,
        'can_confirm_cancellation': post.status == 'PENDING_CANCELLATION' 
            and request.user != post.cancellation_initiator,
    }
    return render(request, 'active_swap.html', context)

@login_required
@require_POST
def send_message(request, post_id):
    post = get_object_or_404(SwapPost, id=post_id)
    message_service = MessageService()
    
    success, result = message_service.send_message(
        post,
        request.user,
        request.POST.get('content')
    )
    
    if success:
        return JsonResponse({'status': 'success', 'message': result})
    return JsonResponse({'status': 'error', 'message': result})

@login_required
def get_messages(request, post_id):
    post = get_object_or_404(SwapPost, id=post_id)
    message_service = MessageService()
    
    success, messages = message_service.get_messages(
        post,
        request.GET.get('last_id')
    )
    
    if success:
        return JsonResponse({'messages': messages})
    return JsonResponse({'error': messages}, status=400)

def error_404(request, exception):
    return render(request, '404.html', status=404)