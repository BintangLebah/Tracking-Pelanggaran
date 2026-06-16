from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin untuk class-based view yang membatasi akses berdasarkan role.

    Usage:
        class AdminView(RoleRequiredMixin, TemplateView):
            allowed_roles = ['admin']
            template_name = 'admin/dashboard.html'
    """
    allowed_roles = []

    def test_func(self):
        return self.request.user.role in self.allowed_roles

    def handle_no_permission(self):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Anda tidak memiliki akses ke halaman ini.")


class GuruRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['guru']


class WaliKelasRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['guru']

    def test_func(self):
        user = self.request.user
        return user.is_guru and user.is_wali_kelas


class BkRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['bk']


class AdminRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['admin']


class OsisRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['osis']