from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user berbasis AbstractUser.
    Tambahkan field baru di sini jika diperlukan di masa depan
    tanpa perlu migrasi besar.

    Role-based access control:
    - Admin: Akses penuh ke semua fitur
    - Guru: Akses guru biasa + privilege tambahan via boolean flags
    - OSIS: Hanya bisa melaporkan pelanggaran ringan
    - BK: Mengatur jenis pelanggaran dan menyetujui laporan

    Privilege booleans untuk Guru:
    - is_homeroom_teacher: Guru yang menjadi wali kelas
    - is_bk_teacher: Guru yang juga bertugas sebagai BK (dual role)
    """

    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        GURU  = 'guru',  'Guru'
        OSIS  = 'osis',  'OSIS'
        BK    = 'bk',    'BK'

    role    = models.CharField(max_length=10, choices=Role.choices, default=Role.GURU)
    no_telp = models.CharField(max_length=20, blank=True)
    foto    = models.ImageField(upload_to='users/', blank=True, null=True)

    # ── Privilege booleans untuk Guru ─────────────────────────────
    is_homeroom_teacher = models.BooleanField(
        default=False,
        help_text='Guru yang menjadi wali kelas. Digunakan untuk menampilkan menu khusus wali kelas.',
    )
    is_bk_teacher = models.BooleanField(
        default=False,
        help_text='Guru yang juga bertugas konseling (dual role Guru+BK).',
    )

    # ── Helper properties — role ──────────────────────────────────

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_guru(self):
        return self.role == self.Role.GURU

    @property
    def is_osis(self):
        return self.role == self.Role.OSIS

    @property
    def is_bk(self):
        return self.role == self.Role.BK

    @property
    def can_manage_settings(self):
        """Admin dan BK boleh akses halaman pengaturan."""
        return self.role in (self.Role.ADMIN, self.Role.BK)

    # ── Helper properties — wali kelas ─────────────────────────────

    @property
    def is_wali_kelas(self):
        """
        True jika guru ini menjadi wali kelas di setidaknya satu kelas aktif.
        Digunakan oleh view dashboard untuk menentukan template yang ditampilkan.

        Contoh penggunaan di view:
            if request.user.is_wali_kelas:
                # render dashboard wali kelas
            else:
                # render dashboard guru biasa
        """
        if not self.is_guru:
            return False
        return self.is_homeroom_teacher or self.kelas_diampu.exists()

    @property
    def kelas_wali(self):
        """
        Mengembalikan objek Kelas pertama yang diampu guru ini.
        Mengembalikan None jika bukan wali kelas.

        Catatan: satu guru idealnya hanya menjadi wali kelas satu kelas.
        Namun jika ada lebih dari satu (data tidak konsisten), ambil yang pertama.

        Contoh penggunaan di view:
            kelas = request.user.kelas_wali
            if kelas:
                siswa_list = kelas.siswa.all()
        """
        return self.kelas_diampu.first()

    @property
    def semua_kelas_wali(self):
        """
        Mengembalikan QuerySet semua kelas yang diampu guru ini.
        Digunakan jika ada kasus guru menjadi wali kelas lebih dari satu kelas.
        """
        return self.kelas_diampu.all()

    @property
    def label_dashboard(self):
        """
        Label yang ditampilkan di header dashboard berdasarkan status guru.

        Contoh hasil:
        - Guru biasa       → "Dashboard Guru"
        - Wali kelas X IPA 1 → "Dashboard Wali Kelas X IPA 1"
        - Admin            → "Dashboard Admin"
        - BK               → "Dashboard BK"
        - OSIS             → "Dashboard OSIS"
        """
        if self.is_wali_kelas and self.kelas_wali:
            return f"Dashboard Wali Kelas {self.kelas_wali.nama_kelas}"
        role_labels = {
            self.Role.ADMIN: 'Dashboard Admin',
            self.Role.GURU:  'Dashboard Guru',
            self.Role.OSIS:  'Dashboard OSIS',
            self.Role.BK:    'Dashboard BK',
        }
        return role_labels.get(self.role, 'Dashboard')

    @property
    def initial(self):
        """Mengembalikan inisial nama user untuk ditampilkan di avatar."""
        if self.get_full_name():
            names = self.get_full_name().split()
            return ''.join(n[0].upper() for n in names[:2])
        return self.username[0].upper() if self.username else 'U'

    class Meta:
        verbose_name        = 'Pengguna'
        verbose_name_plural = 'Pengguna'

    def __str__(self):
        wali_info = f' — Wali {self.kelas_wali}' if self.is_wali_kelas else ''
        return f"{self.get_full_name() or self.username} ({self.get_role_display()}){wali_info}"