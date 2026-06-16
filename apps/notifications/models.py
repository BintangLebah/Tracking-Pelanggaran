from django.db import models
from apps.accounts.models import User


class Notifikasi(models.Model):
    """
    Notifikasi in-app.

    Dibuat otomatis via Django signal (lihat notifikasi/signals.py):
      - Pelanggaran baru memerlukan ACC        → notif ke semua BK
      - PersetujuanBK disimpan                 → notif balik ke pelapor
      - Siswa melewati batas poin wajib BK     → notif ke semua Guru & BK

    Tipe notifikasi:
      LAPORAN_BARU     → BK menerima laporan baru dari Guru/OSIS
      DISETUJUI        → Pelapor diberitahu laporan di-ACC BK
      DITOLAK          → Pelapor diberitahu laporan ditolak BK
      POIN_DITETAPKAN  → BK menetapkan poin untuk jenis custom
      WAJIB_BK         → Siswa melewati batas poin 75, notif ke Guru & BK
    """

    class Tipe(models.TextChoices):
        LAPORAN_BARU    = 'laporan_baru',    'Laporan Baru'
        DISETUJUI       = 'disetujui',       'Disetujui'
        DITOLAK         = 'ditolak',         'Ditolak'
        POIN_DITETAPKAN = 'poin_ditetapkan', 'Poin Ditetapkan'
        WAJIB_BK        = 'wajib_bk',        'Wajib BK'

    penerima     = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifikasi',
    )

    # Relasi ke Pelanggaran — null untuk notif tipe WAJIB_BK
    pelanggaran  = models.ForeignKey(
        'violations.Pelanggaran',
        on_delete=models.CASCADE,
        related_name='notifikasi',
        null=True, blank=True,
    )

    # Relasi ke Siswa — diisi untuk notif tipe WAJIB_BK
    siswa        = models.ForeignKey(
        'academics.Siswa',
        on_delete=models.CASCADE,
        related_name='notifikasi',
        null=True, blank=True,
    )

    tipe         = models.CharField(
        max_length=20,
        choices=Tipe.choices,
        default=Tipe.LAPORAN_BARU,
    )
    pesan        = models.TextField()
    sudah_dibaca = models.BooleanField(default=False)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Notifikasi'
        verbose_name_plural = 'Notifikasi'
        ordering            = ['-created_at']

    def __str__(self):
        ikon = '✓' if self.sudah_dibaca else '●'
        return f"{ikon} {self.penerima.username}: {self.pesan[:60]}"