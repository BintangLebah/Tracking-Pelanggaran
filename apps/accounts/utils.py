from django.shortcuts import redirect
def login_flow(user):
    if user.is_admin: 
        return 'dashboard/admin/'
    elif user.is_guru:
        return 'dashboard/guru/'
    elif user.is_bk:
        return 'dashboard/Guru-bk/'
    else:        
        return 'dashboard/osis/'