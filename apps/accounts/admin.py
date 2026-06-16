from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display  = ('username', 'get_full_name', 'email', 'role', 'is_active', 'date_joined')
    list_filter   = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering      = ('role', 'username')

    # Tambah field role dan no_telp ke form edit user
    fieldsets = UserAdmin.fieldsets + (
        ('Data Tambahan', {
            'fields': ('role', 'no_telp', 'foto'),
        }),
    )

    # Tampil di form tambah user baru
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Data Tambahan', {
            'fields': ('role', 'no_telp'),
        }),
    )