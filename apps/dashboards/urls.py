from . import views
from django.urls import path

app_name = 'dashboards'

urlpatterns = [
    path('', views.index, name='index'),
    path('admin/', views.admin, name='admin'),
    path('guru/', views.dashboard_guru, name='guru'),
    path('osis/', views.osis, name='osis'),
    path('guru-bk/', views.guru_bk, name='guru_bk'),
]
