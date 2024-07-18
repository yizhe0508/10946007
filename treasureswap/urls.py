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
from django.conf import settings
from django.conf.urls.static import static
from mysite.views import error_404
from django.views.defaults import page_not_found


handler404 = 'mysite.views.error_404'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('register_success/', views.register_success, name='register_success'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('activation_success/', views.activate_success, name='activation_success'),
    path('activation_invalid/', views.activate_invalid, name='activation_invalid'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),  
    path('add_swap_post/', views.add_swap_post, name='add_swap_post'),
    path('get_servers/', views.get_servers, name='get_servers'),
    path('swap_manage/', views.swap_manage, name='swap_manage'),
    path('edit_swap_post/', views.edit_swap_post, name='edit_swap_post'),
    path('active_swap/', views.active_swap, name='active_swap'), 
    path('account/', views.update_profile, name='account'),
    path('404/', page_not_found, {'exception': Exception('Page not Found')}),


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)  # 添加靜態文件路由