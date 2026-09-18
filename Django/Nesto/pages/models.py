from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.name

class CityEntity(models.Model):
    """Represents a specific place/thing in the city (e.g., a specific restaurant or hospital)"""
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='entities')
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class Post(models.Model):
    POST_TYPES = (
        ('DISCUSSION', 'Normal Discussion'),
        ('ENTITY_ADD', 'Add New City Guide Entity'),
        ('ENTITY_REVIEW', 'Review Existing Entity'),
    )

    author = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content = models.TextField()
    post_type = models.CharField(max_length=20, choices=POST_TYPES, default='DISCUSSION')

    categories = models.ManyToManyField(Category, blank=True)
    
    entity = models.ForeignKey(CityEntity, on_delete=models.SET_NULL, null=True, blank=True)
    
    city = models.CharField(max_length=100, default='Bhopal')
    created_at = models.DateTimeField(auto_now_add=True)
    upvotes = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)

    def __str__(self):
        return self.title