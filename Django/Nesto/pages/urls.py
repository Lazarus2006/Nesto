from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('create-post/', views.create_post, name='create_post'),
    path('entity/<int:pk>/', views.entity_detail, name='entity_detail'),
    path("city/select/",views.choose_city,name="choose_city",),
    path("post/<int:pk>/comment/",views.add_comment,name="add_comment",),
    path("post/<int:pk>/", views.post_detail, name="post_detail"),
    path('user/<str:username>/', views.public_profile, name='public_profile'),
    path("comment/<int:pk>/edit/", views.edit_comment, name="edit_comment"),
    path("comment/<int:pk>/delete/", views.delete_comment, name="delete_comment"),
]