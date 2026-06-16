from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

from .models import JenisPelanggaran, Pelanggaran
from apps.academics.models import Siswa


@login_required
@require_http_methods(['GET', 'POST'])
def input_pelanggaran(request):
    """Handle pelanggaran input.

    - If called with GET and query param `siswa`, render the OSIS-specific
      template prefilled with that student.
    - On POST, validate and create a Pelanggaran record using existing
      database tables (no new tables created).
    """
    siswa = None
    # Accept siswa id from GET (link) or POST (form)
    siswa_id = request.GET.get('siswa') if request.method == 'GET' else request.POST.get('siswa_id')
    if siswa_id:
        siswa = get_object_or_404(Siswa, pk=siswa_id)

    if request.method == 'POST':
        if not siswa:
            messages.error(request, 'Siswa tidak ditemukan.')
            return redirect(request.META.get('HTTP_REFERER', '/'))

        tgl = request.POST.get('tgl_kejadian') or None
        jenis_val = request.POST.get('jenis_pelanggaran')
        deskripsi = request.POST.get('deskripsi') or ''
        bukti = request.FILES.get('bukti_foto')

        # Expect jenis_val to be an integer PK of JenisPelanggaran (only RINGAN allowed here)
        try:
            jenis = JenisPelanggaran.objects.get(pk=int(jenis_val), kategori=JenisPelanggaran.Kategori.RINGAN, is_active=True)
        except Exception:
            messages.error(request, 'Pilih jenis pelanggaran yang valid (kategori RINGAN).')
            return redirect(request.META.get('HTTP_REFERER', '/'))

        pel = Pelanggaran(
            siswa=siswa,
            jenis_pelanggaran=jenis,
            dilaporkan_oleh=request.user,
            deskripsi_tambahan=deskripsi,
            tanggal_kejadian=tgl or None,
            bukti_foto=bukti,
        )
        pel.save()

        if pel.status == Pelanggaran.Status.MENUNGGU:
            messages.success(request, 'Laporan berhasil dikirim dan menunggu persetujuan BK.')
        else:
            messages.success(request, 'Laporan berhasil dikirim.')

        # Redirect back to referring page when possible
        return redirect(request.META.get('HTTP_REFERER', '/'))

    # GET handling — render appropriate template
    jenis_list = JenisPelanggaran.objects.filter(kategori=JenisPelanggaran.Kategori.RINGAN, is_active=True).order_by('nama')

    if siswa:
        return render(request, 'violation/input_pelanggaran_osis.html', {
            'siswa': siswa,
            'jenis_list': jenis_list,
        })

    return render(request, 'violation/input_pelanggaran.html', {
        'jenis_list': jenis_list,
    })