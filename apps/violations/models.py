from django.db import models
from django.utils import timezone
from apps.accounts.models import User
from apps.academics.models import Siswa


# ──────────────────────────────────────────────────────────
# 1. Jenis Pelanggaran
# ──────────────────────────────────────────────────────────

class JenisPelanggaran(models.Model):
    """
    Katalog jenis pelanggaran.

    is_custom=True  → dibuat saat input karena tidak tercantum di katalog.
                      Menunggu BK menetapkan poin.
    kategori ringan → satu-satunya yang bisa dilaporkan OSIS.
    """

    class Kategori(models.TextChoices):
        RINGAN = 'ringan', 'Ringan'
        SEDANG = 'sedang', 'Sedang'
        BERAT  = 'berat',  'Berat'

    nama                 = models.CharField(max_length=150)
    kategori             = models.CharField(
        max_length=10,
        choices=Kategori.choices,
        default=Kategori.RINGAN,
    )
    deskripsi            = models.TextField(blank=True)
    poin_default         = models.PositiveIntegerField(
        default=0,
        help_text='0 jika custom — BK yang menetapkan poin setelah review.',
    )
    perlu_persetujuan_bk = models.BooleanField(
        default=False,
        help_text='True secara otomatis untuk semua laporan OSIS dan jenis custom.',
    )
    is_custom            = models.BooleanField(
        default=False,
        help_text='True jika dibuat on-the-fly saat input pelanggaran.',
    )
    is_active            = models.BooleanField(default=True)
    dibuat_oleh          = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='jenis_pelanggaran_dibuat',
    )
    created_at           = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Jenis Pelanggaran'
        verbose_name_plural = 'Jenis Pelanggaran'
        ordering            = ['kategori', 'nama']

    def __str__(self):
        prefix = '[Custom] ' if self.is_custom else ''
        return f"{prefix}{self.nama} ({self.get_kategori_display()} – {self.poin_default} poin)"


# ──────────────────────────────────────────────────────────
# 2. Pelanggaran
# ──────────────────────────────────────────────────────────

class Pelanggaran(models.Model):
    """
    Catatan pelanggaran seorang siswa.

    Alur status:
      MENUNGGU  → laporan dari OSIS, atau Guru dengan jenis custom → menunggu ACC BK
      DISETUJUI → BK sudah ACC
      DITOLAK   → BK menolak
      LANGSUNG  → Guru/Admin input jenis standar (tidak perlu melewati BK)
    """

    class Status(models.TextChoices):
        MENUNGGU  = 'menunggu',  'Menunggu Persetujuan'
        DISETUJUI = 'disetujui', 'Disetujui'
        DITOLAK   = 'ditolak',   'Ditolak'
        LANGSUNG  = 'langsung',  'Langsung Berlaku'

    siswa              = models.ForeignKey(
        Siswa,
        on_delete=models.CASCADE,
        related_name='pelanggaran',
    )
    jenis_pelanggaran  = models.ForeignKey(
        JenisPelanggaran,
        on_delete=models.PROTECT,
        related_name='pelanggaran',
    )
    dilaporkan_oleh    = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='pelanggaran_dilaporkan',
    )
    deskripsi_tambahan = models.TextField(
        blank=True,
        help_text='Keterangan tambahan atau isi deskripsi jika jenis custom.',
    )
    poin_ditetapkan    = models.PositiveIntegerField(
        default=0,
        help_text='Disalin dari poin_default saat input; bisa diubah BK saat ACC.',
    )
    status             = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.MENUNGGU,
    )
    tanggal_kejadian   = models.DateField(default=timezone.now)

    # Bukti foto — wajib/opsional dikontrol oleh PengaturanAplikasi.wajib_bukti_foto
    # Validasi dilakukan di form/serializer, bukan di model.
    bukti_foto         = models.ImageField(
        upload_to='bukti_pelanggaran/%Y/%m/',
        blank=True,
        null=True,
    )

    created_at         = models.DateTimeField(auto_now_add=True)
    updated_at         = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Pelanggaran'
        verbose_name_plural = 'Pelanggaran'
        ordering            = ['-created_at']

    def __str__(self):
        return (
            f"{self.siswa.nama} – {self.jenis_pelanggaran.nama} "
            f"({self.get_status_display()})"
        )

    def save(self, *args, **kwargs):
        """
        Tentukan status awal secara otomatis saat pertama kali dibuat:
        - Jenis custom atau dilaporkan OSIS → MENUNGGU (perlu ACC BK)
        - Guru/Admin dengan jenis standar   → LANGSUNG (poin langsung masuk)
        """
        if not self.pk:
            jenis    = self.jenis_pelanggaran
            reporter = self.dilaporkan_oleh

            # Jika jenis custom atau dilaporkan oleh OSIS -> menunggu ACC BK
            if jenis.is_custom or (reporter and reporter.is_osis):
                self.status          = self.Status.MENUNGGU
                self.poin_ditetapkan = 0  # BK yang tetapkan

            # Jika dilaporkan oleh Guru/Admin -> langsung berlaku
            elif reporter and (reporter.is_guru or reporter.is_admin):
                self.status = self.Status.LANGSUNG
                base_poin = jenis.poin_default
                try:
                    siswa_org = getattr(self.siswa, 'organisasi', 'bukan_anggota')
                except Exception:
                    siswa_org = 'bukan_anggota'
                multiplier = 2 if siswa_org in ('osis', 'mpk') else 1
                self.poin_ditetapkan = base_poin * multiplier

        super().save(*args, **kwargs)


# ──────────────────────────────────────────────────────────
# 3. Persetujuan BK
# ──────────────────────────────────────────────────────────

class PersetujuanBK(models.Model):
    """
    Keputusan BK untuk setiap laporan yang memerlukan ACC.
    Satu baris per pelanggaran (OneToOne).
    Saat disimpan, status & poin di tabel Pelanggaran ikut diperbarui,
    lalu total poin siswa dihitung ulang.
    """

    class Keputusan(models.TextChoices):
        SETUJU = 'setuju', 'Setuju'
        TOLAK  = 'tolak',  'Tolak'

    pelanggaran  = models.OneToOneField(
        Pelanggaran,
        on_delete=models.CASCADE,
        related_name='persetujuan',
    )
    bk           = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='persetujuan_bk',
        limit_choices_to={'role': User.Role.BK},
    )
    keputusan    = models.CharField(max_length=6, choices=Keputusan.choices)
    catatan      = models.TextField(blank=True)
    poin_final   = models.PositiveIntegerField(
        default=0,
        help_text='BK bisa mengubah dari poin_default jenis.',
    )
    diproses_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Persetujuan BK'
        verbose_name_plural = 'Persetujuan BK'

    def __str__(self):
        return (
            f"[{self.get_keputusan_display()}] "
            f"{self.pelanggaran.siswa.nama} – {self.pelanggaran.jenis_pelanggaran.nama}"
        )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        p = self.pelanggaran
        if self.keputusan == self.Keputusan.SETUJU:
            p.status = Pelanggaran.Status.DISETUJUI
            try:
                siswa_org = getattr(p.siswa, 'organisasi', 'bukan_anggota')
            except Exception:
                siswa_org = 'bukan_anggota'
            multiplier = 2 if siswa_org in ('osis', 'mpk') else 1
            p.poin_ditetapkan = self.poin_final * multiplier
        else:
            p.status = Pelanggaran.Status.DITOLAK
        p.save(update_fields=['status', 'poin_ditetapkan'])
        p.siswa.hitung_ulang_poin()


# ──────────────────────────────────────────────────────────
# 4. History Poin (reset bulanan)
# ──────────────────────────────────────────────────────────

class HistoryPoin(models.Model):
    """
    Snapshot poin siswa sebelum reset bulanan.
    Dibuat otomatis oleh APScheduler setiap awal bulan.
    Bisa diexport ke Excel / PDF untuk laporan.
    """

    siswa          = models.ForeignKey(
        Siswa,
        on_delete=models.CASCADE,
        related_name='history_poin',
    )
    bulan          = models.PositiveSmallIntegerField(help_text='1–12')
    tahun          = models.PositiveSmallIntegerField()
    total_poin     = models.PositiveIntegerField(
        help_text='Poin yang terakumulasi selama bulan berjalan sebelum direset.',
    )
    jumlah_kasus   = models.PositiveIntegerField(
        default=0,
        help_text='Jumlah pelanggaran yang tercatat di bulan ini.',
    )
    direset_pada   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'History Poin'
        verbose_name_plural = 'History Poin'
        ordering            = ['-tahun', '-bulan', 'siswa__nama']
        unique_together     = ['siswa', 'bulan', 'tahun']

    def __str__(self):
        return f"{self.siswa.nama} – {self.bulan}/{self.tahun} ({self.total_poin} poin)"

    @property
    def label_periode(self):
        import calendar
        return f"{calendar.month_name[self.bulan]} {self.tahun}"