from django.shortcuts import render
from .models import Post, Category

def home(request):
    posts = Post.objects.all().order_by("-created_at")
    categories = Category.objects.all()
    return render(request, "pages/home.html", {
        "posts": posts,
        "categories": categories
    })