from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import redirect, render

from .forms import UserRegistrationForm

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
