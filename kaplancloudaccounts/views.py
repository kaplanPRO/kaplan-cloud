from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import redirect, render

from .forms import UserRegistrationForm

@login_required
def change_password(request):
    form = PasswordChangeForm(user=request.user, data = request.POST or None)

    if request.method == 'POST' and form.is_valid():
        form.save()
        update_session_auth_hash(request, form.user)
        logout(request)
        return redirect('projects')

    return render(request, 'accounts/change-password.html', {'form':form})

def signin(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if request.POST.get('next') != '':
                return HttpResponseRedirect(request.POST['next'])
            else:
                return redirect('projects')
        else:
            return render(request, 'accounts/login.html', {'form':form})

    else:
        form = AuthenticationForm()
        return render(request, 'accounts/login.html', {'form':form, 'next':request.GET.get('next', '')})

def signout(request):
    logout(request)
    return redirect('projects')

def signup(request, token=None):
    form = UserRegistrationForm(request.POST or None,
                                initial={'token':request.GET.get('token')})
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('login')

    return render(request, 'accounts/register.html', {'form':form})
