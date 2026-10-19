from django.shortcuts import render, redirect
from django.contrib.auth import login , authenticate , logout
from .forms import SignUpForm
from pages.models import get_or_create_profile
from django.contrib.auth.decorators import login_required


@login_required
def profile(request):
    return render(request, "core/profile.html", {
        "profile": get_or_create_profile(request.user),
        "posts": request.user.posts.all().order_by("-created_at"),
    })

def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            get_or_create_profile(user)
            login(request, user)
            return redirect("home")
    else:
        form = SignUpForm()

    return render(request, "core/signup.html", {
        "form": form
    })


def user_login(request):
    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect("home")

        return render(request, "core/login.html", {
            "error": "Invalid username or password."
        })

    return render(request, "core/login.html")


def user_logout(request):
    logout(request)
    return redirect("login")
