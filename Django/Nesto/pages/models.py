from django.db import models
from django.contrib.auth.models import User

class City(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True, related_name="residents")
    display_name = models.CharField(max_length=100)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True) # New field
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.display_name


def get_or_create_profile(user):
    profile, _ = Profile.objects.get_or_create(
        user=user,
        defaults={"display_name": user.username},
    )
    return profile


class Category(models.Model):
    name = models.CharField(max_length=100)
    city = models.CharField(max_length=100, default="General")
    default_attributes = models.JSONField(default=list, blank=True)
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        constraints = [models.UniqueConstraint(
                        fields=["name", "city"],
                        name="unique_category_per_city",
                        )
        ]

    def __str__(self):
        return f"{self.name} ({self.city})"


class Entity(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='entities')
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=255, blank=True, null=True)
    latitude = models.DecimalField(max_digits=9,decimal_places=6,null=True,blank=True,)
    longitude = models.DecimalField(max_digits=9,decimal_places=6,null=True,blank=True,)
    price = models.CharField(max_length=100, blank=True, null=True)
    image = models.ImageField(upload_to='entity_images/', blank=True, null=True)
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
    city = models.ForeignKey(City,on_delete=models.CASCADE,related_name="posts",null=True,blank=True,)
    post_type = models.CharField(max_length=20, choices=POST_TYPES, default='community')
    title = models.CharField(max_length=255)
    content = models.TextField()
    image = models.ImageField(upload_to='post_images/', blank=True, null=True)
    
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')
    entity = models.ForeignKey(Entity, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')
    
    author = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True,related_name="posts")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[{self.get_post_type_display()}] {self.title}"



class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.author.username}: {self.content[:40]}"