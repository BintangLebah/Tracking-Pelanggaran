from functools import wraps
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden


def role_required(*roles):
    """
    Decorator untuk membatasi akses view berdasarkan role user.

    Usage:
        @role_required('admin')
        def admin_view(request):
            ...

        @role_required('guru', 'admin')
        def guru_or_admin_view(request):
            ...

    Untuk role Guru dengan privilege wali kelas:
        @role_required('guru') + cek is_homeroom_teacher di view
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if request.user.role not in roles:
                return HttpResponseForbidden(
                    "Anda tidak memiliki akses ke halaman ini."
                )
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def guru_required(view_func):
    """Decorator khusus untuk role Guru (termasuk wali kelas)."""
    return role_required('guru')(view_func)


def wali_kelas_required(view_func):
    """
    Decorator untuk role Guru yang merupakan wali kelas.
    Gunakan di view yang hanya boleh diakses wali kelas.
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_guru:
            return HttpResponseForbidden("Hanya Guru yang dapat mengakses halaman ini.")
        if not request.user.is_wali_kelas:
            return HttpResponseForbidden("Hanya Wali Kelas yang dapat mengakses halaman ini.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def bk_required(view_func):
    """Decorator khusus untuk role BK."""
    return role_required('bk')(view_func)


def admin_required(view_func):
    """Decorator khusus untuk role Admin."""
    return role_required('admin')(view_func)


def osis_required(view_func):
    """Decorator khusus untuk role OSIS."""
    return role_required('osis')(view_func)