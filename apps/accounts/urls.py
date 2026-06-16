from . import views
from django.urls import path

app_name = 'account'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('403/', views.no_permission, name='no_permission'),
    path('logout/', views.logout_view, name='logout'),
    path('kelola-user/', views.kelola_user, name='kelola_user'),
    path('tambah-user/', views.tambah_user, name='tambah_user'),
]