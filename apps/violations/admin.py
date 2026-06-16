from django.contrib import admin
from django.utils.html import format_html
from .models import JenisPelanggaran, Pelanggaran, PersetujuanBK, HistoryPoin


@admin.register(JenisPelanggaran)
class JenisPelanggaranAdmin(admin.ModelAdmin):
    list_display  = ('nama', 'kategori', 'poin_default', 'is_custom',
                     'perlu_persetujuan_bk', 'is_active')
    list_filter   = ('kategori', 'is_custom', 'perlu_persetujuan_bk', 'is_active')
    search_fields = ('nama',)
    ordering      = ('kategori', 'nama')


class PersetujuanBKInline(admin.StackedInline):
    model       = PersetujuanBK
    extra       = 0
    max_num     = 1
    can_delete  = False
    readonly_fields = ('diproses_at',)


@admin.register(Pelanggaran)
class PelanggaranAdmin(admin.ModelAdmin):
    list_display   = (
        'siswa', 'jenis_pelanggaran', 'dilaporkan_oleh',
        'poin_ditetapkan', 'status_badge', 'tanggal_kejadian', 'ada_bukti',
    )
    list_filter    = ('status', 'jenis_pelanggaran__kategori', 'tanggal_kejadian')
    search_fields  = ('siswa__nama', 'siswa__nis', 'jenis_pelanggaran__nama')
    ordering       = ('-created_at',)
    readonly_fields = ('status', 'poin_ditetapkan', 'created_at', 'updated_at')
    inlines        = [PersetujuanBKInline]

    def status_badge(self, obj):
        warna = {
            'menunggu':  '#f59e0b',
            'disetujui': '#10b981',
            'ditolak':   '#ef4444',
            'langsung':  '#6366f1',
        }
        c = warna.get(obj.status, '#9ca3af')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:9999px;font-size:11px">{}</span>',
            c, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def ada_bukti(self, obj):
        return bool(obj.bukti_foto)
    ada_bukti.boolean     = True
    ada_bukti.short_description = 'Bukti'


@admin.register(PersetujuanBK)
class PersetujuanBKAdmin(admin.ModelAdmin):
    list_display  = ('pelanggaran', 'bk', 'keputusan', 'poin_final', 'diproses_at')
    list_filter   = ('keputusan',)
    search_fields = ('pelanggaran__siswa__nama',)
    readonly_fields = ('diproses_at',)


@admin.register(HistoryPoin)
class HistoryPoinAdmin(admin.ModelAdmin):
    list_display   = ('siswa', 'bulan', 'tahun', 'total_poin', 'jumlah_kasus', 'direset_pada')
    list_filter    = ('tahun', 'bulan')
    search_fields  = ('siswa__nama', 'siswa__nis')
    ordering       = ('-tahun', '-bulan')
    readonly_fields = ('direset_pada',)