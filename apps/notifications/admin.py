from django.contrib import admin
from django.utils.html import format_html
from .models import Notifikasi


@admin.register(Notifikasi)
class NotifikasiAdmin(admin.ModelAdmin):
    list_display   = ('penerima', 'tipe_badge', 'pesan_singkat', 'sudah_dibaca', 'created_at')
    list_filter    = ('tipe', 'sudah_dibaca')
    search_fields  = ('penerima__username', 'pesan')
    ordering       = ('-created_at',)
    readonly_fields = ('created_at',)

    def pesan_singkat(self, obj):
        return obj.pesan[:80] + ('…' if len(obj.pesan) > 80 else '')
    pesan_singkat.short_description = 'Pesan'

    def tipe_badge(self, obj):
        warna = {
            'laporan_baru':    '#6366f1',
            'disetujui':       '#10b981',
            'ditolak':         '#ef4444',
            'poin_ditetapkan': '#f59e0b',
            'wajib_bk':        '#dc2626',
        }
        c = warna.get(obj.tipe, '#9ca3af')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:9999px;font-size:11px">{}</span>',
            c, obj.get_tipe_display()
        )
    tipe_badge.short_description = 'Tipe'