"""
URL configuration for Project_HDAM project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

# Django에서는, 이 path를 배치하는 순서도 중요하다.
# 예를 들어, error/를 <str:date>/보다 아래로 놓을 경우, str:date로 인식하게 된다.
urlpatterns = [
    path('', views.main, name='main'),
    path('error/', views.main_error, name='main_error'),
    path('<str:date>/', views.date_view, name='date-view'),
    path('<str:date>/summary/', views.main_summary, name='main_sum'),
    path('<str:date>/summary/img/', views.main_image, name='main_img'),
    # path('img/', views.main_image, name='main_img'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)