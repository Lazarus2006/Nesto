from django import forms
from .models import Post, Comment, ServiceRequest, ServiceResponse, ServiceMessage


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content']


class CommentForm(forms.ModelForm):
    content = forms.CharField(max_length=5000)

    class Meta:
        model = Comment
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Share your thoughts..."
            })
        }


class ServiceRequestForm(forms.ModelForm):
    description = forms.CharField(max_length=10000)

    class Meta:
        model = ServiceRequest
        fields = ["title", "description", "category", "location", "budget"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "category": forms.TextInput(attrs={"placeholder": "e.g. Repairs, Editing, Lessons"}),
            "location": forms.TextInput(attrs={"placeholder": "Neighbourhood or meeting area"}),
            "budget": forms.TextInput(attrs={"placeholder": "Optional"}),
        }


class ServiceResponseForm(forms.ModelForm):
    content = forms.CharField(max_length=5000)

    class Meta:
        model = ServiceResponse
        fields = ["kind", "content"]
        widgets = {"content": forms.Textarea(attrs={"rows": 3})}


class ServiceMessageForm(forms.ModelForm):
    content = forms.CharField(max_length=5000)

    class Meta:
        model = ServiceMessage
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Coordinate the details here. Keep personal contact information private.",
            })
        }