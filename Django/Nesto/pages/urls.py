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
    path("services/", views.service_list, name="service_list"),
    path("services/new/", views.service_create, name="service_create"),
    path("services/<int:pk>/", views.service_detail, name="service_detail"),
    path("services/<int:pk>/respond/", views.service_respond, name="service_respond"),
    path(
        "services/<int:pk>/accept/<int:response_pk>/",
        views.service_accept,
        name="service_accept",
    ),
    path(
        "services/<int:pk>/status/",
        views.service_update_status,
        name="service_update_status",
    ),
    path("services/<int:pk>/message/", views.service_message, name="service_message"),
]