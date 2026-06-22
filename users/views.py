from django.shortcuts import render, redirect
from django.contrib import messages
from .form import UserRegisterForm, UserUpdateForm, ProfileUpdateForm
from .models import UserProfile
from django.contrib.auth import logout
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

# Create your views here.


def register(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.email = form.cleaned_data.get("email")
            new_user.save()

            submitted_phone = form.cleaned_data.get("phone_number")

            UserProfile.objects.get_or_create(
                user=new_user, defaults={"phone_number": submitted_phone}
            )

            username = form.cleaned_data.get("username")
            messages.success(request, f"Account created for {username}!")
            return redirect("user-login")
    else:
        form = UserRegisterForm()
    return render(request, "users/register.html", {"form": form})


@require_POST
def logout_view(request):
    if request.method == "POST":
        logout(request)
        messages.success(
            request,
            "You have signed out.",
        )
    return redirect("/")


@login_required
def user_settings_view(request):
    if not hasattr(request.user, "profile"):
        UserProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(
            request.POST, request.FILES, instance=request.user.userprofile
        )

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f"Your account has been updated! ")
            return redirect("user-profile")

    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.userprofile)

    context = {
        "u_form": u_form,
        "p_form": p_form,
    }

    return render(request, "users/profile.html", context)
