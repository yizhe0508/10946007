from django.shortcuts import render

def index(request):
    return render(request, 'index.html')

def signup(request):
    return render(request, 'signup.html')

def login(request):
    return render(request, 'login.html')

def add_swap(request):
    return render(request, 'add_swap.html')

def error_404(request, exception):
    return render(request, 'error_404.html')