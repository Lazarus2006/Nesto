from django.shortcuts import render

def login_view(request):
    return render(request, "login.html")


def username_view(request):
    return render(request, "username.html")
