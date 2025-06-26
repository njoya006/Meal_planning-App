"""
URL configuration for meal_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import csrf_views
from .test_views import CORSTestView, MediaTestView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/csrf-token/', csrf_views.get_csrf_token, name='csrf_token'),
    path('api/csrf-debug/', csrf_views.csrf_debug, name='csrf_debug'),
    path('api/test-upload-no-csrf/', csrf_views.test_upload_no_csrf, name='test_upload_no_csrf'),
    path('api/test-cors/', CORSTestView.as_view(), name='test_cors'),
    path('api/test-media/', MediaTestView.as_view(), name='test_media'),
    path('api/users/', include('users.urls')),
    path('api/dj-rest-auth/', include('dj_rest_auth.urls')),
    path('api/dj-rest-auth/registration/', include('dj_rest_auth.registration.urls')),
    path('api/planner/', include('planner.urls')),
    path('api/recipes/', include('recipes.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
