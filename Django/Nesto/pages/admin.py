from django.contrib import admin
from .models import (
    City,
    Profile,
    Category,
    Entity,
    Post,
    Comment,
    ServiceRequest,
    ServiceResponse,
    ServiceMessage,
)


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "latitude", "longitude")
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("display_name", "user", "city")
    list_filter = ("city",)
    search_fields = ("display_name", "user__username")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "is_approved", "created_at")
    list_filter = ("city", "is_approved")
    search_fields = ("name", "city")


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "location", "price", "is_approved")
    list_filter = ("category", "is_approved")
    search_fields = ("name", "location")
    list_editable = ("is_approved",)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "post_type", "city", "category", "author", "created_at")
    list_filter = ("city", "post_type", "category")
    search_fields = ("title", "content", "author__username")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("post", "author", "created_at")
    search_fields = ("content", "author__username", "post__title")


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ("title", "city", "requester", "status", "created_at")
    list_filter = ("city", "status", "category")
    search_fields = ("title", "description", "requester__username")


@admin.register(ServiceResponse)
class ServiceResponseAdmin(admin.ModelAdmin):
    list_display = ("service_request", "responder", "kind", "created_at")
    list_filter = ("kind",)
    search_fields = ("content", "responder__username", "service_request__title")


@admin.register(ServiceMessage)
class ServiceMessageAdmin(admin.ModelAdmin):
    list_display = ("service_request", "sender", "created_at")
    search_fields = ("content", "sender__username", "service_request__title")