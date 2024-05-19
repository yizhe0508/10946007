from django.shortcuts import render

def index(request):
    return render(request, 'index.html')

def signup(request):
    return render(request, 'signup.html')

def login(request):
    return render(request, 'login.html')

def add_swap(request):
    if request.method == 'POST':
        item_image = request.FILES['item-image']
        # 這裡處理你的文件上傳邏輯
    return render(request, 'add_swap.html')

def edit_swap(request):
    if request.method == 'POST':
        item_image = request.FILES['item-image']
        # 這裡處理你的文件上傳邏輯
    return render(request, 'edit_swap.html')

def swap_manage(request):
    return render(request, 'swap_manage.html')

def error_404(request, exception):
    return render(request, 'error_404.html')