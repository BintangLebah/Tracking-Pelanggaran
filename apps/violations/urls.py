from . import views
from django.urls import path

app_name = 'violation'

urlpatterns = [
    path('input_pelanggaran/', views.input_pelanggaran, name='input_pelanggaran'),
]