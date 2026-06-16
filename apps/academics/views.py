from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.contrib import messages

from .models import Siswa, Kelas
from apps.accounts.models import User
from apps.accounts.decorators import osis_required, role_required

@role_required('admin', 'guru')
def data_kelas(request):
    """Menampilkan daftar kelas beserta statistik singkat untuk Admin & Guru.

    Mendukung pencarian dengan query string `q` dan paginasi (5 kelas per halaman).
    """
    qs = Kelas.objects.annotate(jml_siswa=Count('siswa')).order_by('tingkat', 'nama_kelas')
    q = request.GET.get('q')
    if q:
        qs = qs.filter(
            Q(nama_kelas__icontains=q) |
            Q(tahun_ajaran__icontains=q) |
            Q(wali_kelas__username__icontains=q) |
            Q(wali_kelas__first_name__icontains=q) |
            Q(wali_kelas__last_name__icontains=q)
        )

    paginator = Paginator(qs, 5)  # 5 kelas per halaman
    page = request.GET.get('page')
    kelas_page = paginator.get_page(page)

    return render(request, 'academic/data_kelas.html', {
        'kelas_list': kelas_page,
        'q': q,
    })


@osis_required
def data_osis(request, kelas_id=None):
    """Render daftar siswa berdasarkan kelas yang dipilih.

    - Menampilkan semua siswa dari kelas yang dipilih, bukan hanya siswa OSIS.
    - Mendukung query string `q` untuk pencarian nama/NIS.
    - Mendukung pagination (10 item per halaman).
    - Jika `kelas_id` diberikan, tampilkan informasi kelas di header.
    """
    kelas = None
    
    if kelas_id:
        kelas = get_object_or_404(Kelas, pk=kelas_id)
        qs = Siswa.objects.filter(kelas=kelas).select_related('kelas').order_by('nama')
    else:
        # Jika tidak ada kelas_id, tidak ada data yang ditampilkan (error page)
        return render(request, 'academic/data_osis.html', {
            'kelas': None,
            'students': None,
            'q': None,
            'error': 'Silakan pilih kelas terlebih dahulu'
        })

    q = request.GET.get('q')
    if q:
        qs = qs.filter(Q(nama__icontains=q) | Q(nis__icontains=q))

    paginator = Paginator(qs, 10)
    page = request.GET.get('page')
    students = paginator.get_page(page)

    return render(request, 'academic/data_osis.html', {
        'kelas': kelas,
        'students': students,
        'q': q,
    })


@role_required('admin', 'guru')
def detail_kelas(request, pk):
    """Tampilkan halaman detail kelas (daftar siswa di kelas).

    Reuse template data_osis.html for layout.
    """
    kelas = get_object_or_404(Kelas, pk=pk)
    qs = Siswa.objects.filter(kelas=kelas).select_related('kelas').order_by('nama')
    q = request.GET.get('q')
    if q:
        qs = qs.filter(Q(nama__icontains=q) | Q(nis__icontains=q))
    paginator = Paginator(qs, 10)
    page = request.GET.get('page')
    students = paginator.get_page(page)
    return render(request, 'academic/data_osis.html', {
        'kelas': kelas,
        'students': students,
        'q': q,
    })


@role_required('admin', 'guru')
def tambah_kelas(request):
    """Render form tambah kelas (GET) and handle create (POST)."""
    wali_options = User.objects.filter(role=User.Role.GURU, is_active=True)

    if request.method == 'POST':
        nama = request.POST.get('nama_kelas', '').strip()
        tingkat = request.POST.get('tingkat', '').strip()
        tahun = request.POST.get('tahun_ajaran', '').strip()
        wali_id = request.POST.get('wali_kelas') or None

        errors = {}
        if not nama:
            errors['nama_kelas'] = 'Nama kelas wajib diisi.'
        if tingkat not in ('10', '11', '12'):
            errors['tingkat'] = 'Tingkat tidak valid.'
        if not tahun:
            errors['tahun_ajaran'] = 'Tahun ajaran wajib diisi.'

        if errors:
            return render(request, 'academic/tambah+edit_kelas.html', {
                'title': 'Tambah Kelas',
                'form_data': request.POST,
                'errors': errors,
                'wali_options': wali_options,
                'action_url': reverse('academic:tambah_kelas'),
                'submit_label': 'Simpan'
            })

        # create Kelas
        kelas = Kelas.objects.create(
            nama_kelas=nama,
            tingkat=tingkat,
            tahun_ajaran=tahun,
            dibuat_oleh=request.user if request.user.is_authenticated else None,
        )
        if wali_id:
            try:
                wali = User.objects.get(pk=wali_id)
                kelas.wali_kelas = wali
                kelas.save(update_fields=['wali_kelas'])
            except User.DoesNotExist:
                pass

        return redirect(reverse('academic:data_kelas'))

    # GET
    return render(request, 'academic/tambah+edit_kelas.html', {
        'title': 'Tambah Kelas',
        'form_data': {},
        'errors': None,
        'wali_options': wali_options,
        'action_url': reverse('academic:tambah_kelas'),
        'submit_label': 'Simpan'
    })


@role_required('admin', 'guru')
def edit_kelas(request, pk):
    """Render edit form and handle update for a Kelas."""
    kelas = get_object_or_404(Kelas, pk=pk)
    wali_options = User.objects.filter(role=User.Role.GURU, is_active=True)

    if request.method == 'POST':
        nama = request.POST.get('nama_kelas', '').strip()
        tingkat = request.POST.get('tingkat', '').strip()
        tahun = request.POST.get('tahun_ajaran', '').strip()
        wali_id = request.POST.get('wali_kelas') or None

        errors = {}
        if not nama:
            errors['nama_kelas'] = 'Nama kelas wajib diisi.'
        if tingkat not in ('10', '11', '12'):
            errors['tingkat'] = 'Tingkat tidak valid.'
        if not tahun:
            errors['tahun_ajaran'] = 'Tahun ajaran wajib diisi.'

        if errors:
            return render(request, 'academic/tambah+edit_kelas.html', {
                'title': 'Edit Kelas',
                'form_data': request.POST,
                'errors': errors,
                'wali_options': wali_options,
                'kelas': kelas,
                'action_url': reverse('academic:edit_kelas', args=[kelas.pk]),
                'submit_label': 'Perbarui'
            })

        kelas.nama_kelas = nama
        kelas.tingkat = tingkat
        kelas.tahun_ajaran = tahun
        if wali_id:
            try:
                kelas.wali_kelas = User.objects.get(pk=wali_id)
            except User.DoesNotExist:
                kelas.wali_kelas = None
        else:
            kelas.wali_kelas = None
        kelas.save()

        return redirect(reverse('academic:data_kelas'))

    return render(request, 'academic/tambah+edit_kelas.html', {
        'title': 'Edit Kelas',
        'form_data': {},
        'errors': None,
        'wali_options': wali_options,
        'kelas': kelas,
        'action_url': reverse('academic:edit_kelas', args=[kelas.pk]),
        'submit_label': 'Perbarui'
    })


# ---------------------------
# Hapus kelas (konfirmasi & aksi)
# ---------------------------
@role_required('admin', 'guru')
def hapus_kelas(request):
    """Menangani GET (tampilkan halaman konfirmasi) dan POST (hapus).

    - GET: menerima pk di query string (?pk=) dan menampilkan template 'academic/hapus_kelas.html'
    - POST: menerima pk di body; jika jumlah siswa == 0 hapus langsung, atau jika ada 'confirm'=1 hapus setelah konfirmasi
    """
    pk = request.POST.get('pk') if request.method == 'POST' else request.GET.get('pk')
    if not pk:
        messages.error(request, 'Kelas tidak ditemukan.')
        return redirect(reverse('academic:data_kelas'))

    try:
        kelas = Kelas.objects.get(pk=pk)
    except (Kelas.DoesNotExist, ValueError):
        messages.error(request, 'Kelas tidak ditemukan.')
        return redirect(reverse('academic:data_kelas'))

    siswa_count = kelas.siswa.count()

    if request.method == 'POST':
        # Jika POST dan jumlah siswa 0 => hapus langsung
        confirm = request.POST.get('confirm') == '1'
        if siswa_count == 0 or confirm:
            nama = kelas.nama_kelas
            kelas.delete()
            messages.success(request, f'Kelas "{nama}" berhasil dihapus.')
            return redirect(reverse('academic:data_kelas'))
        # Jika POST tanpa konfirmasi tapi siswa > 0 -> tampilkan halaman konfirmasi
        return render(request, 'academic/hapus_kelas.html', {
            'kelas': kelas,
            'siswa_count': siswa_count
        })

    # GET -> tampilkan halaman konfirmasi
    return render(request, 'academic/hapus_kelas.html', {
        'kelas': kelas,
        'siswa_count': siswa_count
    })


# ---------------------------
# Siswa views (list / add / detail / edit)
# ---------------------------
@role_required('admin', 'guru', 'bk')
def data_siswa(request):
    """Menampilkan daftar siswa dengan pencarian dan pagination.

    Jika query string `kelas` diberikan, filter daftar siswa ke kelas tersebut
    dan sertakan objek kelas di context sehingga template dapat menampilkan
    link "Tambah Siswa (Kelas terpilih)" yang mengarah ke view tambah_siswa_kelas.
    """
    qs = Siswa.objects.select_related('kelas').order_by('nama')
    q = request.GET.get('q')

    # dukungan untuk ?kelas=<pk>
    kelas_param = request.GET.get('kelas')
    kelas_obj = None
    if kelas_param:
        try:
            kelas_obj = Kelas.objects.get(pk=kelas_param)
            qs = qs.filter(kelas=kelas_obj)
        except (Kelas.DoesNotExist, ValueError):
            kelas_obj = None

    if q:
        qs = qs.filter(Q(nama__icontains=q) | Q(nis__icontains=q))

    paginator = Paginator(qs, 10)
    page = request.GET.get('page')
    siswa_list = paginator.get_page(page)

    return render(request, 'academic/data_siswa.html', {
        'siswa_list': siswa_list,
        'q': q,
        'kelas': kelas_obj,
    })


@role_required('admin', 'guru')
def tambah_siswa(request, kelas_id=None):
    """Render form tambah siswa and handle create.

    The form in template is not strictly standardized, so this handler
    accepts common field names and falls back gracefully.
    """
    kelas_options = Kelas.objects.all()
    kelas_obj = None
    if kelas_id:
        try:
            kelas_obj = Kelas.objects.get(pk=kelas_id)
        except (Kelas.DoesNotExist, ValueError):
            kelas_obj = None

    if request.method == 'POST':
        nis = request.POST.get('nis', '').strip()
        nama = request.POST.get('nama', '').strip()
        jenis = request.POST.get('gender') or request.POST.get('jenis_kelamin') or 'L'
        tgl = request.POST.get('tgl_lahir') or None
        status_keorg = request.POST.get('status_keorganisasian', '').lower()
        is_osis = status_keorg == 'osis'
        kelas_id_post = request.POST.get('kelas') or request.POST.get('kelas_id') or None

        errors = {}
        if not nis:
            errors['nis'] = 'NIS wajib diisi.'
        if not nama:
            errors['nama'] = 'Nama wajib diisi.'
        if jenis not in ('L', 'P'):
            # allow 'Laki'/'Perempuan' heuristics
            if jenis.lower().startswith('l'):
                jenis = 'L'
            else:
                jenis = 'P'

        if not kelas_id_post:
            errors['kelas'] = 'Kelas wajib dipilih.'
        else:
            try:
                kelas_obj = Kelas.objects.get(pk=kelas_id_post)
            except (Kelas.DoesNotExist, ValueError):
                errors['kelas'] = 'Kelas tidak valid.'

        if errors:
            return render(request, 'academic/tambah_siswa.html', {
                'errors': errors,
                'form_data': request.POST,
                'kelas_options': kelas_options,
                'kelas': kelas_obj,
                'siswa': None,
            })

        # terima file foto jika ada
        foto_file = request.FILES.get('foto')

        siswa = Siswa.objects.create(
            nis=nis,
            nama=nama,
            jenis_kelamin=jenis,
            tanggal_lahir=tgl if tgl else None,
            kelas=kelas_obj,
            organisasi=status_keorg if status_keorg else 'bukan_anggota',
            is_osis=is_osis,
            foto=foto_file if foto_file else None,
            ditambah_oleh=request.user if request.user.is_authenticated else None,
        )
        # ensure total poin / wajib bk flags are correct
        siswa.hitung_ulang_poin()

        # Jika siswa dibuat untuk kelas tertentu, kembali ke daftar siswa yang terfilter pada kelas itu
        if kelas_obj:
            return redirect(f"{reverse('academic:data_siswa')}?kelas={kelas_obj.pk}")
        return redirect(reverse('academic:data_siswa'))

    return render(request, 'academic/tambah_siswa.html', {
        'kelas_options': kelas_options,
        'form_data': {},
        'errors': None,
        'kelas': kelas_obj,
        'siswa': None,
    })


@role_required('admin', 'guru', 'bk')
def detail_siswa(request, pk):
    siswa = get_object_or_404(Siswa.objects.select_related('kelas'), pk=pk)
    # Fetch violations for this student, ordered by date descending
    from apps.violations.models import Pelanggaran, HistoryPoin
    pelanggaran_list = Pelanggaran.objects.filter(siswa=siswa).select_related('jenis_pelanggaran', 'dilaporkan_oleh').order_by('-tanggal_kejadian')
    history_poin_list = HistoryPoin.objects.filter(siswa=siswa).order_by('-bulan')
    
    # determine whether to force 'wajib BK' visual state based on total points
    try:
        total_poin = int(siswa.total_poin or 0)
    except (TypeError, ValueError):
        total_poin = 0

    wajib_by_points = total_poin >= 75

    return render(request, 'academic/detail_siswa.html', {
        'siswa': siswa,
        'kelas': siswa.kelas,
        'pelanggaran_list': pelanggaran_list,
        'history_poin_list': history_poin_list,
        'wajib_by_points': wajib_by_points,
    })


@role_required('admin', 'guru')
def edit_siswa(request, pk):
    """Basic edit handler for siswa (minimal implementation)."""
    siswa = get_object_or_404(Siswa, pk=pk)
    kelas_options = Kelas.objects.all()

    if request.method == 'POST':
        errors = {}
        siswa.nis = request.POST.get('nis', siswa.nis).strip()
        siswa.nama = request.POST.get('nama', siswa.nama).strip()
        jenis = request.POST.get('gender') or siswa.jenis_kelamin
        if jenis in ('L', 'P'):
            siswa.jenis_kelamin = jenis
        status_keorg = request.POST.get('status_keorganisasian', '').lower()
        # simpan organisasi dan sinkronisasi flag is_osis
        if status_keorg in ('osis', 'mpk', 'bukan_anggota'):
            siswa.organisasi = status_keorg
        siswa.is_osis = (siswa.organisasi == 'osis')

        # terima file foto jika ada
        if 'foto' in request.FILES:
            siswa.foto = request.FILES['foto']

        tgl = request.POST.get('tgl_lahir')
        siswa.tanggal_lahir = tgl or siswa.tanggal_lahir
        kelas_id = request.POST.get('kelas')
        if not kelas_id:
            errors['kelas'] = 'Kelas wajib dipilih.'
        else:
            try:
                siswa.kelas = Kelas.objects.get(pk=kelas_id)
            except (Kelas.DoesNotExist, ValueError):
                errors['kelas'] = 'Kelas tidak valid.'

        if errors:
            return render(request, 'academic/tambah_siswa.html', {
                'siswa': siswa,
                'kelas_options': kelas_options,
                'form_data': request.POST,
                'errors': errors,
                'kelas': siswa.kelas,
            })

        siswa.save()
        siswa.hitung_ulang_poin()
        # Redirect back to siswa list page with kelas filter
        if siswa.kelas:
            return redirect(f"{reverse('academic:data_siswa')}?kelas={siswa.kelas.pk}")
        return redirect(reverse('academic:data_siswa'))

    return render(request, 'academic/tambah_siswa.html', {
        'siswa': siswa,
        'kelas_options': kelas_options,
        'form_data': {},
        'errors': None,
        'kelas': siswa.kelas,
    })
