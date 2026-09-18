from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    city = models.CharField(max_length=100, default="General")
    # Stores default suggested attribute keys for this category e.g. ["Opening Time", "Rules"]
    default_attributes = models.JSONField(default=list, blank=True)
    is_approved = models.BooleanField(default=True) 
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return f"{self.name} ({self.city})"


class Entity(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='entities')
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=255, blank=True, null=True)
    price = models.CharField(max_length=100, blank=True, null=True)
    image = models.ImageField(upload_to='entity_images/', blank=True, null=True)
    # Stores key-value attributes filled by users e.g. {"Opening Time": "9 AM", "Closing Time": "10 PM"}
    attributes = models.JSONField(default=dict, blank=True)
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Entities"

    def __str__(self):
        return f"{self.name} - {self.category.name}"


class Post(models.Model):
    POST_TYPES = (
        ('community', 'Community Discussion'),
        ('guide', 'City Guide Entry'),
    )

    post_type = models.CharField(max_length=20, choices=POST_TYPES, default='community')
    title = models.CharField(max_length=255)
    content = models.TextField()
    image = models.ImageField(upload_to='post_images/', blank=True, null=True)
    
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')
    entity = models.ForeignKey(Entity, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')
    
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.get_post_type_display()}] {self.title}"