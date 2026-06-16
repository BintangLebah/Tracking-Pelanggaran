"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from apps.accounts import views as accounts_views

urlpatterns = [
    path('admin/', admin.site.urls),
    # Root explicitly mapped to login view to avoid ambiguous includes
    path('', accounts_views.login_view, name='root_login'),
    path('403/', accounts_views.no_permission, name='no_permission'),
    path('logout/', accounts_views.logout_view, name='logout'),
    path('account/', include('apps.accounts.urls')),
    path('dashboard/', include('apps.dashboards.urls')),
    path('academics/', include(('apps.academics.urls', 'academic'), namespace='academic')),
    path('violations/', include(('apps.violations.urls', 'violation'), namespace='violation')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
