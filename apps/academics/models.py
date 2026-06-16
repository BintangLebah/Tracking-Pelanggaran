from django.db import models
from django.db.models import Sum
from apps.accounts.models import User
import os
from django.utils import timezone


def siswa_file_upload_path(instance, filename):
    """Upload path for siswa.foto

    Files saved under static/image/photo/ or static/image/vid/ according to extension.
    Use nis prefix to reduce collisions.
    """
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    photo_exts = {'jpg','jpeg','png','gif','webp','bmp','svg','mp3'}  # mp3 per permintaan
    vid_exts = {'mp4','mov','avi','mkv','webm'}
    if ext in vid_exts:
        sub = 'vid'
    else:
        sub = 'photo'
    name = f"{instance.nis or 'siswa'}_{int(timezone.now().timestamp())}.{ext}" if ext else f"{instance.nis or 'siswa'}_{int(timezone.now().timestamp())}"
    return os.path.join('image', sub, name)


class Kelas(models.Model):
    """
    Data kelas. Bisa dibuat oleh Guru atau Admin.
    """

    TINGKAT_CHOICES = [
        ('10', 'Kelas 10'),
        ('11', 'Kelas 11'),
        ('12', 'Kelas 12'),
    ]

    nama_kelas   = models.CharField(max_length=50)
    tingkat      = models.CharField(max_length=2, choices=TINGKAT_CHOICES)
    tahun_ajaran = models.CharField(max_length=9, help_text="Format: 2024/2025")
    wali_kelas   = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='kelas_diampu',
        limit_choices_to={'role': User.Role.GURU},
    )
    dibuat_oleh  = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='kelas_dibuat',
    )
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Kelas'
        verbose_name_plural = 'Kelas'
        ordering            = ['tingkat', 'nama_kelas']
        unique_together     = ['nama_kelas', 'tahun_ajaran']

    def __str__(self):
        return f"{self.nama_kelas} ({self.tahun_ajaran})"

    def total_poin_kelas(self):
        """
        Akumulasi total_poin seluruh siswa di kelas ini.
        Digunakan untuk statistik per kelas (Admin, Guru, BK).
        """
        return self.siswa.aggregate(
            total=Sum('total_poin')
        )['total'] or 0

    def jumlah_siswa_wajib_bk(self):
        """Jumlah siswa di kelas ini yang masuk kategori wajib BK (poin >= 75)."""
        return self.siswa.filter(total_poin__gte=75).count()


class Siswa(models.Model):
    """
    Data siswa sekolah.
    total_poin dihitung ulang otomatis setiap ada pelanggaran di-ACC atau dibatalkan.

    Wajib BK: siswa dengan total_poin >= BATAS_WAJIB_BK otomatis
    masuk daftar wajib BK dan memicu notifikasi ke Guru & BK.
    """

    BATAS_WAJIB_BK = 75

    JENIS_KELAMIN = [
        ('L', 'Laki-laki'),
        ('P', 'Perempuan'),
    ]

    nis              = models.CharField(max_length=20, unique=True)
    nama             = models.CharField(max_length=100)
    jenis_kelamin    = models.CharField(max_length=1, choices=JENIS_KELAMIN)
    is_osis          = models.BooleanField(
        default=False,
        help_text='True jika siswa ini anggota OSIS.',
    )

    # Organisasi / keanggotaan organisasi siswa (OSIS/MPK/dll.)
    ORGANISASI_CHOICES = [
        ('bukan_anggota', 'Bukan Anggota'),
        ('osis', 'OSIS'),
        ('mpk', 'MPK'),
    ]
    organisasi       = models.CharField(max_length=20, choices=ORGANISASI_CHOICES, default='bukan_anggota', help_text='Organisasi yang diikuti siswa, jika ada.')

    tanggal_lahir    = models.DateField(null=True, blank=True)
    kelas            = models.ForeignKey(
        Kelas,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='siswa',
    )
    foto             = models.ImageField(upload_to=siswa_file_upload_path, blank=True, null=True)
    total_poin       = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        """
        Pastikan flag is_osis sinkron dengan field organisasi.
        """
        try:
            self.is_osis = (self.organisasi == 'osis')
        except Exception:
            # fallback jika atribut belum diset
            pass
        super().save(*args, **kwargs)

    # Flag wajib BK — di-set otomatis oleh hitung_ulang_poin()
    # Digunakan untuk filter cepat tanpa harus hitung ulang tiap query
    is_wajib_bk      = models.BooleanField(
        default=False,
        help_text='True jika total_poin >= 75. Di-set otomatis.',
    )

    ditambah_oleh    = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='siswa_ditambahkan',
    )
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Siswa'
        verbose_name_plural = 'Siswa'
        ordering            = ['nama']

    def __str__(self):
        return f"{self.nama} ({self.nis})"

    def hitung_ulang_poin(self):
        """
        Dipanggil setelah pelanggaran di-ACC, ditolak, atau dibatalkan.
        - Menjumlahkan poin dari pelanggaran DISETUJUI + LANGSUNG
        - Update flag is_wajib_bk
        - Jika baru pertama kali melewati batas wajib BK → kirim notifikasi
        """
        from apps.violations.models import Pelanggaran

        sebelumnya_wajib_bk = self.is_wajib_bk

        total = self.pelanggaran.filter(
            status__in=[
                Pelanggaran.Status.DISETUJUI,
                Pelanggaran.Status.LANGSUNG,
            ]
        ).aggregate(total=Sum('poin_ditetapkan'))['total'] or 0

        self.total_poin  = total
        self.is_wajib_bk = total >= self.BATAS_WAJIB_BK
        self.save(update_fields=['total_poin', 'is_wajib_bk'])

        # Kirim notifikasi hanya saat pertama kali status berubah menjadi wajib BK
        if self.is_wajib_bk and not sebelumnya_wajib_bk:
            self._kirim_notif_wajib_bk()

    def _kirim_notif_wajib_bk(self):
        """
        Kirim notifikasi ke semua user Guru dan BK bahwa siswa ini
        sudah melewati batas poin wajib BK.
        Dipanggil otomatis dari hitung_ulang_poin().
        """
        from apps.notifications.models import Notifikasi

        penerima = User.objects.filter(
            role__in=[User.Role.GURU, User.Role.BK],
            is_active=True,
        )
        notif_list = [
            Notifikasi(
                penerima=user,
                siswa=self,
                tipe=Notifikasi.Tipe.WAJIB_BK,
                pesan=(
                    f"⚠️ {self.nama} ({self.kelas or 'tanpa kelas'}) "
                    f"telah mencapai {self.total_poin} poin dan masuk "
                    f"daftar WAJIB BK."
                ),
            )
            for user in penerima
        ]
        Notifikasi.objects.bulk_create(notif_list)