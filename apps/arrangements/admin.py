from django.contrib import admin
from .models import PengaturanAplikasi


@admin.register(PengaturanAplikasi)
class PengaturanAplikasiAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Bukti Pelanggaran', {
            'fields': ('wajib_bukti_foto',),
        }),
        ('Hak Input Pelanggaran Custom', {
            'fields': ('izinkan_custom_guru', 'izinkan_custom_osis'),
        }),
        ('Reset Poin Bulanan', {
            'fields': ('reset_poin_aktif', 'tanggal_reset'),
        }),
        ('Audit', {
            'fields': ('diubah_oleh', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ('updated_at',)

    def has_add_permission(self, request):
        """Cegah pembuatan baris kedua."""
        return not PengaturanAplikasi.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False