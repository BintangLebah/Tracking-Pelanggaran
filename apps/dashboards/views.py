from django.shortcuts import render, redirect
from apps.accounts.decorators import role_required
from apps.academics.models import Kelas


def index(request):
    """Root dashboard landing — redirect user to role-specific dashboard."""
    if not request.user.is_authenticated:
        return redirect('login')
    role = getattr(request.user, 'role', None)
    mapping = {
        'admin': 'admin',
        'guru': 'guru',
        'osis': 'osis',
        'bk': 'guru-bk',
    }
    sub = mapping.get(role, 'admin')
    return redirect(f'/dashboard/{sub}/')


# Create your views here.
@role_required('admin')
def admin(request):
    context = {
        'title': 'Home',
    }
    return render(request, 'dashboard/admin.html', context)

@role_required('osis')
def osis(request):
    """Dashboard OSIS - Menampilkan daftar kelas dan siswa OSIS."""
    # Fetch semua kelas dari database
    kelas_list = Kelas.objects.all().prefetch_related('siswa').order_by('tingkat', 'nama_kelas')
    
    context = {
        'title': 'Dashboard OSIS',
        'kelas_list': kelas_list,
    }
    return render(request, 'dashboard/osis.html', context)

@role_required('bk')
def guru_bk(request):
    context = {
        'title': 'Home',
    }
    return render(request, 'dashboard/guru-bk.html', context)

# Guru dashboard logic (kept here)


from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Sum, Count, Q

from apps.academics.models import Siswa, Kelas
from apps.violations.models import Pelanggaran
from apps.notifications.models import Notifikasi


@login_required
def dashboard_guru(request):
    """
    View tunggal untuk dashboard guru.
    Satu URL, dua tampilan — ditentukan oleh status wali kelas guru yang login.
    """
    user = request.user

    # Notifikasi belum dibaca (dipakai di kedua template)
    notif_belum_dibaca = Notifikasi.objects.filter(
        penerima=user,
        sudah_dibaca=False,
    ).count()

    # ── CABANG 1: Guru adalah wali kelas ─────────────────────────────────────
    if user.is_wali_kelas:
        kelas      = user.kelas_wali          # objek Kelas yang diampu
        siswa_qs   = kelas.siswa.all()        # semua siswa di kelas ini

        # Pelanggaran siswa di kelas ini saja
        pelanggaran_qs = Pelanggaran.objects.filter(
            siswa__kelas=kelas
        )

        # Pelanggaran bulan berjalan
        from django.utils import timezone
        now = timezone.now()
        pelanggaran_bulan_ini = pelanggaran_qs.filter(
            created_at__month=now.month,
            created_at__year=now.year,
        )

        context = {
            'mode'               : 'wali_kelas',            # flag untuk template
            'kelas'              : kelas,
            'label_dashboard'    : user.label_dashboard,

            # Statistik kartu
            'total_siswa'        : siswa_qs.count(),
            'total_pelanggaran'  : pelanggaran_bulan_ini.count(),
            'menunggu_acc'       : pelanggaran_bulan_ini.filter(
                                       status=Pelanggaran.Status.MENUNGGU
                                   ).count(),
            'siswa_wajib_bk'     : siswa_qs.filter(is_wajib_bk=True).count(),

            # Statistik kelas (untuk kartu ringkasan kelas)
            'akumulasi_poin_kelas': kelas.total_poin_kelas(),
            'jumlah_wajib_bk_kelas': kelas.jumlah_siswa_wajib_bk(),

            # Tabel pelanggaran terbaru — hanya siswa di kelas ini
            'pelanggaran_terbaru': pelanggaran_qs.select_related(
                                       'siswa', 'siswa__kelas',
                                       'jenis_pelanggaran', 'dilaporkan_oleh'
                                   ).order_by('-created_at')[:10],

            # Siswa wajib BK di kelas ini
            'siswa_wajib_bk_list': siswa_qs.filter(
                                       is_wajib_bk=True
                                   ).order_by('-total_poin')[:5],

            # Notifikasi
            'notif_count'        : notif_belum_dibaca,
        }
        return render(request, 'dashboard/guru_wali_kelas.html', context)

    # ── CABANG 2: Guru biasa (bukan wali kelas) ───────────────────────────────
    else:
        from django.utils import timezone
        now = timezone.now()

        # Statistik umum sekolah
        semua_pelanggaran = Pelanggaran.objects.all()
        pelanggaran_bulan = semua_pelanggaran.filter(
            created_at__month=now.month,
            created_at__year=now.year,
        )

        # Statistik per kelas (semua kelas)
        semua_kelas = Kelas.objects.annotate(
            jml_siswa=Count('siswa'),
        ).order_by('tingkat', 'nama_kelas')

        context = {
            'mode'               : 'guru_biasa',
            'label_dashboard'    : user.label_dashboard,   # "Dashboard Guru"

            # Statistik kartu
            'total_siswa'        : Siswa.objects.count(),
            'total_pelanggaran'  : pelanggaran_bulan.count(),
            'menunggu_acc'       : pelanggaran_bulan.filter(
                                       status=Pelanggaran.Status.MENUNGGU
                                   ).count(),
            'siswa_wajib_bk'     : Siswa.objects.filter(is_wajib_bk=True).count(),

            # Tabel statistik per kelas
            'semua_kelas'        : semua_kelas,

            # Tabel pelanggaran terbaru (semua kelas)
            'pelanggaran_terbaru': semua_pelanggaran.select_related(
                                       'siswa', 'siswa__kelas',
                                       'jenis_pelanggaran', 'dilaporkan_oleh'
                                   ).order_by('-created_at')[:10],

            # Notifikasi
            'notif_count'        : notif_belum_dibaca,
        }
        return render(request, 'dashboard/guru_biasa.html', context)
