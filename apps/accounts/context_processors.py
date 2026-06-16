from .models import User


def user_role_context(request):
    """
    Context processor untuk menyediakan data role user ke semua template.
    Digunakan untuk menampilkan sidebar yang berbeda berdasarkan role.
    
    Catatan: Selalu mengirim variabel dengan nilai default, bahkan jika user tidak authenticated,
    untuk menghindari masalah TemplateDoesNotExist saat variabel tidak ada di context.
    """
    context = {
        'is_admin': False,
        'is_guru': False,
        'is_osis': False,
        'is_bk': False,
        'is_homeroom_teacher': False,
        'is_wali_kelas': False,
        'kelas_wali': None,
        'user_role': None,
    }
    
    if not request.user.is_authenticated:
        return context

    user = request.user
    context.update({
        'user_role': user.role,
        'is_admin': user.is_admin,
        'is_guru': user.is_guru,
        'is_osis': user.is_osis,
        'is_bk': user.is_bk,
        'is_homeroom_teacher': user.is_homeroom_teacher,
        'is_wali_kelas': user.is_wali_kelas,
        'kelas_wali': user.kelas_wali,
    })
    
    return context