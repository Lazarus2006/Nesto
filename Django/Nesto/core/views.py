from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from .forms import SignUpForm
from pages.models import get_or_create_profile, Post
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST


@login_required
def profile(request):
    profile_obj = get_or_create_profile(request.user)

    if request.method == "POST":
        display_name = request.POST.get("display_name")
        username = request.POST.get("username")
        email = request.POST.get("email")
        profile_picture = request.FILES.get("profile_picture")

        if username:
            request.user.username = username
        if email:
            request.user.email = email
        request.user.save()

        if display_name:
            profile_obj.display_name = display_name
        if profile_picture:
            profile_obj.profile_picture = profile_picture
        profile_obj.save()

        messages.success(request, "Profile updated successfully!")
        return redirect("profile")

    return render(request, "core/profile.html", {
        "profile": profile_obj,
        "posts": request.user.posts.all().order_by("-created_at"),
    })

@login_required
def edit_post(request, pk):
    post = get_object_or_404(Post, pk=pk, author=request.user)
    if request.method == "POST":
        post.title = request.POST.get("title", post.title)
        post.content = request.POST.get("content", post.content)
        post.save()
        messages.success(request, "Post updated successfully!")
    return redirect("profile")

@login_required
def delete_post(request, pk):
    post = get_object_or_404(Post, pk=pk, author=request.user)
    if request.method == "POST":
        post.delete()
        messages.success(request, "Post deleted successfully!")
    return redirect("profile")

def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            get_or_create_profile(user)
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
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


@require_POST
def user_logout(request):
    logout(request)
    return redirect("login")

@login_required
def delete_account(request):
    if request.method == "POST":
        user = request.user
        Post.objects.filter(author=user).delete()
        logout(request)
        user.delete()
        messages.success(request, "Your account and all associated data have been permanently deleted.")
        return redirect("home") # Redirect to your landing/home page
        
    return redirect("profile")
