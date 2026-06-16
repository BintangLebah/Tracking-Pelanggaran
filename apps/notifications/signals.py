"""
Signal handlers untuk pengiriman notifikasi otomatis.

Daftarkan di NotifikasiConfig.ready() pada notifikasi/apps.py:

    class NotifikasiConfig(AppConfig):
        name = 'notifikasi'
        def ready(self):
            import notifikasi.signals  # noqa
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.violations.models import Pelanggaran, PersetujuanBK
from apps.accounts.models import User
from .models import Notifikasi


@receiver(post_save, sender=Pelanggaran)
def notif_laporan_baru(sender, instance, created, **kwargs):
    """
    Setiap pelanggaran baru yang memerlukan ACC → kirim notif ke semua BK.
    Pelanggaran LANGSUNG (jenis standar Guru/Admin) tidak perlu notif ke BK,
    tapi tetap bisa memicu notif WAJIB_BK lewat hitung_ulang_poin() di bawah.
    """
    if not created:
        return

    # Notif laporan ke BK hanya jika perlu ACC
    if instance.status == Pelanggaran.Status.MENUNGGU:
        bk_users  = User.objects.filter(role=User.Role.BK, is_active=True)
        pelapor   = instance.dilaporkan_oleh
        notif_list = [
            Notifikasi(
                penerima=bk,
                pelanggaran=instance,
                tipe=Notifikasi.Tipe.LAPORAN_BARU,
                pesan=(
                    f"Laporan baru: {instance.siswa.nama} – "
                    f"{instance.jenis_pelanggaran.nama}. "
                    f"Dilaporkan oleh {pelapor or 'sistem'}."
                ),
            )
            for bk in bk_users
        ]
        Notifikasi.objects.bulk_create(notif_list)

    # Untuk pelanggaran LANGSUNG, poin sudah ditetapkan di save()
    # → langsung hitung ulang poin siswa (termasuk cek wajib BK)
    if instance.status == Pelanggaran.Status.LANGSUNG:
        instance.siswa.hitung_ulang_poin()


@receiver(post_save, sender=PersetujuanBK)
def notif_hasil_persetujuan(sender, instance, created, **kwargs):
    """
    Setelah BK ACC/tolak → kirim notif balik ke pelapor asli.
    Catatan: hitung_ulang_poin() sudah dipanggil di PersetujuanBK.save(),
    sehingga pengecekan wajib BK sudah terjadi di sana.
    """
    if not created:
        return

    pelanggaran = instance.pelanggaran
    pelapor     = pelanggaran.dilaporkan_oleh
    if not pelapor:
        return

    if instance.keputusan == PersetujuanBK.Keputusan.SETUJU:
        tipe  = Notifikasi.Tipe.DISETUJUI
        pesan = (
            f"Laporan {pelanggaran.siswa.nama} – "
            f"{pelanggaran.jenis_pelanggaran.nama} "
            f"disetujui. Poin: {instance.poin_final}."
        )
    else:
        tipe  = Notifikasi.Tipe.DITOLAK
        pesan = (
            f"Laporan {pelanggaran.siswa.nama} – "
            f"{pelanggaran.jenis_pelanggaran.nama} "
            f"ditolak oleh BK. Catatan: {instance.catatan or '-'}."
        )

    Notifikasi.objects.create(
        penerima=pelapor,
        pelanggaran=pelanggaran,
        tipe=tipe,
        pesan=pesan,
    )