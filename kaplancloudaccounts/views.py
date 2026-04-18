from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.utils.html import strip_tags

from kaplancloudapp.forms import _apply_daisy_classes

from .forms import UserRegistrationForm


@login_required
def change_password(request):
    form = PasswordChangeForm(user=request.user, data=request.POST or None)
    _apply_daisy_classes(form)
    for field in form.fields.values():
        if field.help_text:
            field.help_text = strip_tags(field.help_text)

    if request.method == "POST" and form.is_valid():
        form.save()
        update_session_auth_hash(request, form.user)
        logout(request)
        return redirect("projects")

    return render(request, "accounts/change-password.html", {"form": form})


def signin(request):
    if request.method == "POST":
        form = AuthenticationForm(request, request.POST)
        _apply_daisy_classes(form)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if request.POST.get("next") != "":
                return HttpResponseRedirect(request.POST["next"])
            else:
                return redirect("projects")
        else:
            return render(request, "accounts/login.html", {"form": form})

    else:
        form = AuthenticationForm()
        _apply_daisy_classes(form)
        return render(
            request,
            "accounts/login.html",
            {"form": form, "next": request.GET.get("next", "")},
        )


def signout(request):
    logout(request)
    return redirect("projects")


def signup(request, token=None):
    form = UserRegistrationForm(
        request.POST or None, initial={"token": request.GET.get("token")}
    )
    if request.method == "POST":
        if form.is_valid():
            form.save()
            return redirect("login")

    return render(request, "accounts/register.html", {"form": form})
