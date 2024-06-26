"""
URL configuration for treasureswap project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from mysite import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('add_swap/', views.add_swap, name='add_swap'),
    path('swap_manage/', views.swap_manage, name='swap_manage'),
    path('edit_swap/', views.edit_swap, name='edit_swap'),
    path('active_swap/', views.active_swap, name='active_swap'), 
    path('account/', views.account, name='account'),   
    path('404/', views.error_404, name='error_404'),
]
