from django.urls import path
from . import views

app_name = 'academic'

urlpatterns = [
    # Kelas
    path('kelas/', views.data_kelas, name='data_kelas'),
    path('kelas/tambah/', views.tambah_kelas, name='tambah_kelas'),
    path('kelas/<int:pk>/', views.detail_kelas, name='detail_kelas'),
    path('kelas/<int:pk>/edit/', views.edit_kelas, name='edit_kelas'),
    # Hapus kelas (konfirmasi & aksi)
    path('kelas/hapus/', views.hapus_kelas, name='hapus_kelas'),

    # Siswa
    path('siswa/', views.data_siswa, name='data_siswa'),
    path('siswa/tambah/', views.tambah_siswa, name='tambah_siswa'),
    path('kelas/<int:kelas_id>/siswa/tambah/', views.tambah_siswa, name='tambah_siswa_kelas'),
    path('siswa/<int:pk>/', views.detail_siswa, name='detail_siswa'),
    path('siswa/<int:pk>/edit/', views.edit_siswa, name='edit_siswa'),

    # OSIS
    path('osis/', views.data_osis, name='data_osis'),
    path('osis/kelas/<int:kelas_id>/', views.data_osis, name='data_osis_kelas'),
]
