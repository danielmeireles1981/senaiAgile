from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('', lambda request: redirect('login', permanent=False)),  # Redireciona para a página de login
]
