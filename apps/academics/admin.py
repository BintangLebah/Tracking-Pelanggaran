from django.contrib import admin
from django.utils.html import format_html
from .models import Kelas, Siswa


@admin.register(Kelas)
class KelasAdmin(admin.ModelAdmin):
    list_display  = (
        'nama_kelas', 'tingkat', 'tahun_ajaran', 'wali_kelas',
        'jumlah_siswa', 'total_poin_kelas', 'jumlah_siswa_wajib_bk',
    )
    list_filter   = ('tingkat', 'tahun_ajaran')
    search_fields = ('nama_kelas', 'wali_kelas__first_name', 'wali_kelas__last_name')
    ordering      = ('tingkat', 'nama_kelas')

    def jumlah_siswa(self, obj):
        return obj.siswa.count()
    jumlah_siswa.short_description = 'Jumlah Siswa'

    def total_poin_kelas(self, obj):
        return obj.total_poin_kelas()
    total_poin_kelas.short_description = 'Total Poin Kelas'

    def jumlah_siswa_wajib_bk(self, obj):
        n = obj.jumlah_siswa_wajib_bk()
        if n:
            return format_html(
                '<span style="color:#ef4444;font-weight:600">{} siswa</span>', n
            )
        return '-'
    jumlah_siswa_wajib_bk.short_description = 'Wajib BK'


@admin.register(Siswa)
class SiswaAdmin(admin.ModelAdmin):
    list_display   = (
        'nis', 'nama', 'jenis_kelamin', 'kelas',
        'total_poin', 'status_wajib_bk', 'created_at',
    )
    list_filter    = ('jenis_kelamin', 'is_wajib_bk', 'kelas__tingkat', 'kelas__tahun_ajaran')
    search_fields  = ('nis', 'nama')
    ordering       = ('nama',)
    readonly_fields = ('total_poin', 'is_wajib_bk')

    def status_wajib_bk(self, obj):
        if obj.is_wajib_bk:
            return format_html(
                '<span style="background:#ef4444;color:#fff;padding:2px 8px;'
                'border-radius:9999px;font-size:11px">WAJIB BK</span>'
            )
        return '-'
    status_wajib_bk.short_description = 'Status BK'