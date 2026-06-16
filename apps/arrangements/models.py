from django.db import models


class PengaturanAplikasi(models.Model):
    """
    Konfigurasi global aplikasi — SINGLETON (hanya satu baris).
    Diakses Admin dan BK melalui halaman pengaturan.

    Toggle yang tersedia:
      - wajib_bukti_foto      : Apakah user wajib upload foto bukti saat input pelanggaran
      - izinkan_custom_guru   : Apakah Guru boleh menginput jenis pelanggaran yang belum tersedia
      - izinkan_custom_osis   : Apakah OSIS boleh mendeskripsikan pelanggaran yang belum ada
    """

    wajib_bukti_foto    = models.BooleanField(
        default=True,
        verbose_name='Wajib upload foto bukti',
        help_text='Jika aktif, pengguna harus melampirkan foto saat melapor pelanggaran.',
    )
    izinkan_custom_guru = models.BooleanField(
        default=True,
        verbose_name='Guru boleh input jenis pelanggaran baru',
        help_text='Jika aktif, Guru bisa memilih "Lainnya" dan mendeskripsikan pelanggaran sendiri.',
    )
    izinkan_custom_osis = models.BooleanField(
        default=False,
        verbose_name='OSIS boleh mendeskripsikan pelanggaran yang belum ada',
        help_text='Jika aktif, OSIS bisa menuliskan deskripsi untuk pelanggaran yang belum tercantum.',
    )

    # ── Pengaturan reset poin bulanan ────────────────────
    reset_poin_aktif    = models.BooleanField(
        default=True,
        verbose_name='Reset poin bulanan aktif',
        help_text='Jika aktif, total poin siswa direset setiap awal bulan via APScheduler.',
    )
    tanggal_reset       = models.PositiveSmallIntegerField(
        default=1,
        verbose_name='Tanggal reset (hari ke-)',
        help_text='Tanggal dalam bulan saat reset dijalankan (1–28).',
    )

    # ── Audit ────────────────────────────────────────────
    diubah_oleh  = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='+',
        verbose_name='Terakhir diubah oleh',
    )
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Pengaturan Aplikasi'
        verbose_name_plural = 'Pengaturan Aplikasi'

    def __str__(self):
        return 'Pengaturan Aplikasi'

    def save(self, *args, **kwargs):
        """Pastikan hanya ada satu baris (singleton pattern)."""
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Larang penghapusan pengaturan."""
        pass

    @classmethod
    def get(cls):
        """Ambil atau buat pengaturan default."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj