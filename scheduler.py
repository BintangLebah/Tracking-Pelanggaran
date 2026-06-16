"""
scheduler.py  — letakkan di root project (sejajar manage.py)

Jalankan otomatis dari AppConfig.ready() salah satu app, misalnya di
pelanggaran/apps.py:

    from django.apps import AppConfig

    class PelanggaranConfig(AppConfig):
        name = 'pelanggaran'

        def ready(self):
            import scheduler  # noqa: F401  — inisialisasi scheduler

Dependensi:
    pip install apscheduler django-apscheduler

Tambahkan ke INSTALLED_APPS:
    'django_apscheduler',

Lalu jalankan migrasi:
    python manage.py migrate
"""

import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution

logger = logging.getLogger(__name__)


def reset_poin_bulanan():
    """
    Tugas terjadwal:
    1. Baca tanggal reset dari PengaturanAplikasi.
    2. Simpan snapshot poin bulan ini ke HistoryPoin.
    3. Set total_poin semua siswa ke 0.
    """
    from apps.arrangements.models import PengaturanAplikasi
    from apps.academics.models import Siswa
    from apps.violations.models import HistoryPoin, Pelanggaran
    from django.db.models import Sum, Count

    setting = PengaturanAplikasi.get()
    if not setting.reset_poin_aktif:
        logger.info('[Scheduler] Reset poin dilewati — fitur tidak aktif.')
        return

    now   = datetime.now()
    bulan = now.month
    tahun = now.year

    # Bulan yang baru saja selesai
    if bulan == 1:
        bulan_lalu, tahun_lalu = 12, tahun - 1
    else:
        bulan_lalu, tahun_lalu = bulan - 1, tahun

    siswa_list = Siswa.objects.filter(total_poin__gt=0)
    history_baru = []

    for siswa in siswa_list:
        # Hitung jumlah kasus bulan lalu
        jumlah = siswa.pelanggaran.filter(
            status__in=[Pelanggaran.Status.DISETUJUI, Pelanggaran.Status.LANGSUNG],
            tanggal_kejadian__month=bulan_lalu,
            tanggal_kejadian__year=tahun_lalu,
        ).count()

        history_baru.append(
            HistoryPoin(
                siswa=siswa,
                bulan=bulan_lalu,
                tahun=tahun_lalu,
                total_poin=siswa.total_poin,
                jumlah_kasus=jumlah,
            )
        )

    # Simpan semua history sekaligus
    HistoryPoin.objects.bulk_create(
        history_baru,
        ignore_conflicts=True,  # skip jika bulan ini sudah ada (idempoten)
    )

    # Reset poin
    Siswa.objects.update(total_poin=0)
    logger.info(
        '[Scheduler] Reset poin selesai. '
        f'{len(history_baru)} siswa dicatat ke HistoryPoin untuk {bulan_lalu}/{tahun_lalu}.'
    )


def mulai_scheduler():
    """
    Inisialisasi APScheduler dengan DjangoJobStore.
    Dijadwalkan berdasarkan tanggal_reset di PengaturanAplikasi.
    """
    from apps.arrangements.models import PengaturanAplikasi

    setting = PengaturanAplikasi.get()
    tanggal = min(setting.tanggal_reset, 28)  # maks 28 agar aman untuk semua bulan

    scheduler = BackgroundScheduler(timezone='Asia/Jakarta')
    scheduler.add_jobstore(DjangoJobStore(), 'default')

    scheduler.add_job(
        reset_poin_bulanan,
        trigger=CronTrigger(day=tanggal, hour=0, minute=5),
        id='reset_poin_bulanan',
        name='Reset poin siswa setiap bulan',
        jobstore='default',
        replace_existing=True,
    )

    scheduler.start()
    logger.info(f'[Scheduler] APScheduler dimulai. Reset poin dijadwalkan setiap tgl {tanggal}.')