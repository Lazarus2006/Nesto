from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('create-post/', views.create_post, name='create_post'),
    path('entity/<int:pk>/', views.entity_detail, name='entity_detail'),
    path("city/select/",views.choose_city,name="choose_city",),
]