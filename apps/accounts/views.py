from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required


@require_http_methods(["GET", "POST"])
def login_view(request):
    """Simple login view.

    Expects POST with 'username' and 'password'. On success redirects to next or '/'.
    Renders 'accounts/login.html' with optional 'next' context.
    """
    if request.user.is_authenticated:
        return redirect('/dashboard/')

    next_url = request.GET.get('next') or request.POST.get('next') or '/dashboard/'

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            if getattr(user, 'is_active', True):
                login(request, user)
                messages.success(request, 'Berhasil login.')
                return redirect(next_url)
            messages.error(request, 'Akun Anda dinonaktifkan.')
        else:
            messages.error(request, 'Username atau password salah.')

    return render(request, 'account/login.html', {'next': next_url})


def no_permission(request):
    """Render a simple Access Denied page with HTTP 403 status."""
    return render(request, 'account/403.html', status=403)


@login_required
def logout_view(request):
    """Log out the current user and redirect to homepage or login."""
    logout(request)
    messages.success(request, 'Anda telah logout.')
    return redirect('/')

def kelola_user(request):
    """Render a simple user management page."""
    return render(request, 'account/kelola_user.html')

@login_required
def tambah_user(request):
    """Render the add-user form page."""
    # In real implementation this would handle POST to create user.
    return render(request, 'account/tambah_user.html')
