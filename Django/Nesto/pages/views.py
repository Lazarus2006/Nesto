from django.contrib import messages
from .models import Post, Category, Entity, City, Comment, get_or_create_profile , Profile
from django.shortcuts import render, redirect, get_object_or_404
from .forms import PostForm , CommentForm
import json
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch , Q
from django.contrib.auth.models import User

@login_required
def home(request):
    profile = get_or_create_profile(request.user)
    if not profile.city:
        return redirect("choose_city")
    
    city = profile.city
    query = request.GET.get('q', '').strip()
    search_results = {}

    if query:
        search_results['profiles'] = Profile.objects.filter(
            Q(display_name__icontains=query) | Q(user__username__icontains=query),
            city=city
        ).distinct()
        
        search_results['cities'] = City.objects.filter(
            name__icontains=query
        ).distinct()
        
        search_results['categories'] = Category.objects.filter(
            name__icontains=query,
            city=city.name
        ).distinct()
        
        search_results['entities'] = Entity.objects.filter(
            Q(name__icontains=query) | Q(location__icontains=query),
            category__city=city.name
        ).distinct()
        
        search_results['posts'] = Post.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query),
            city=city
        ).distinct()

    posts = (
        Post.objects
        .filter(city=city)
        .select_related("author", "category", "entity")
        .order_by("-created_at")
    )
    categories = (
        Category.objects
        .filter(city=city.name, is_approved=True)
        .prefetch_related("entities")
    )

    context = {
        "posts": posts,
        "categories": categories,
        "city": city,
        "query": query,
        "search_results": search_results,
    }

    return render(request, "pages/home.html", context)


@login_required
def entity_detail(request, pk):
    city = get_or_create_profile(request.user).city
    if not city:
        return redirect("choose_city")

    entity = get_object_or_404(
        Entity,
        pk=pk,
        is_approved=True,
        category__city=city.name,
    )

    posts = Post.objects.filter(
        entity = entity,
        city = city,
    ).order_by("-created_at")

    categories = Category.objects.filter(
        city = city.name,
        is_approved = True,
    ).prefetch_related("entities")

    context = {
        "entity": entity,
        "posts": posts,
        "categories": categories,
        "city": city,
    }

    return render(
        request,
        "pages/entity_detail.html",
        context
    )

@login_required
def create_post(request):
    profile = get_or_create_profile(request.user)
    if not profile.city:
        return redirect("choose_city")
    city = profile.city
    if request.method == 'POST':
        post_type = request.POST.get('post_type', 'community')
        title = request.POST.get('title')
        content = request.POST.get('content')
        image = request.FILES.get('image')

        if post_type == 'community':
            Post.objects.create(
                post_type = "community",
                title = title,
                content = content,
                image = image,
                author = request.user,
                city = city,
            )
            messages.success(request, "Community post created successfully!")
            return redirect('home')

        elif post_type == 'guide':
            category_id = request.POST.get('category')
            new_category_name = request.POST.get('new_category')
            entity_id = request.POST.get('entity')
            new_entity_name = request.POST.get('new_entity')
            location = request.POST.get('location')
            price = request.POST.get('price')
            raw_lat = request.POST.get('latitude')
            raw_lng = request.POST.get('longitude')
            latitude = float(raw_lat) if raw_lat else None
            longitude = float(raw_lng) if raw_lng else None

            category = None
            if category_id == 'new' and new_category_name:
                category, _ = Category.objects.get_or_create(
                    name = new_category_name.strip(),
                    city = city.name,)
            elif category_id and category_id != 'new':
                category = Category.objects.filter(
                    id = category_id,
                    city = city.name,
                    is_approved = True,
                ).first()

            attr_keys = request.POST.getlist('attr_keys[]')
            attr_values = request.POST.getlist('attr_values[]')
            custom_attributes = {}
            new_suggested_attrs = set(category.default_attributes) if (category and category.default_attributes) else set()

            for key, val in zip(attr_keys, attr_values):
                key_clean = key.strip()
                val_clean = val.strip()
                if key_clean and val_clean:
                    custom_attributes[key_clean] = val_clean
                    new_suggested_attrs.add(key_clean)

            if category:
                category.default_attributes = list(new_suggested_attrs)
                category.save()

            entity = None
            if category:
                if entity_id == 'new' and new_entity_name:
                    entity = Entity.objects.create(
                        category = category,
                        name = new_entity_name.strip(),
                        location = location,
                        latitude = latitude,
                        longitude = longitude,
                        price = price,
                        image = image,
                        attributes = custom_attributes
                    )
                elif entity_id and entity_id != 'new':
                    entity = Entity.objects.filter(id=entity_id).first()
                    if entity:
                        entity.attributes.update(custom_attributes)
                        if location: entity.location = location
                        if price: entity.price = price
                        if latitude is not None: entity.latitude = latitude
                        if longitude is not None: entity.longitude = longitude
                        entity.save()

            Post.objects.create(
                post_type = 'guide',
                title = title,
                content = content,
                category = category,
                entity = entity,
                image = image,
                author = request.user,
                city = city,
            )
            messages.success(request, "City Guide post published successfully!")
            return redirect('home')

    categories = Category.objects.filter(
        city = city.name,
        is_approved = True).prefetch_related('entities')
    
    categories_json = {}
    for cat in categories:
        categories_json[cat.id] = {
            'name': cat.name,
            'default_attributes': cat.default_attributes or [],
            'entities': [
                {
                    'id': ent.id,
                    'name': ent.name,
                    'location': ent.location or '',
                    'price': ent.price or '',
                    'latitude': str(ent.latitude) if ent.latitude else '',
                    'longitude': str(ent.longitude) if ent.longitude else '',
                    'attributes': ent.attributes or {}
                }
                for ent in cat.entities.filter(is_approved=True)
            ]
        }

    context = {
        'categories': categories,
        'categories_json': json.dumps(categories_json),
        'prefill_type': request.GET.get('type', ''),
        'prefill_category': request.GET.get('category', ''),
        'prefill_entity': request.GET.get('entity', ''),
    }
    return render(request, 'pages/create_post.html', context)


@login_required
def choose_city(request):
    profile = get_or_create_profile(request.user)
    cities = City.objects.all().order_by("name")
    if request.method == "POST":
        city_id = request.POST.get("city")
        city = get_object_or_404(City,id=city_id)

        profile.city = city
        profile.save(update_fields=["city"])

        return redirect("home")

    return render(request, "pages/choose_city.html", {
        "cities": cities,
    })


@login_required
def add_comment(request, pk):
    post = get_object_or_404(Post, pk=pk)

    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            messages.success(request, "Comment added!")
        else:
            messages.error(request, "Please enter a valid comment.")

    return redirect("post_detail", pk=post.pk)


@login_required
def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    comments = post.comments.select_related("author").all()

    return render(request, "pages/post_detail.html", {
        "post": post,
        "comments": comments,
        "comment_form": CommentForm(),
    })


@login_required
def public_profile(request, username):
    target_user = get_object_or_404(User, username=username)
    target_profile = get_object_or_404(Profile, user=target_user)
    
    viewer_profile = get_or_create_profile(request.user)
    posts = Post.objects.filter(
        author=target_user, 
        city=viewer_profile.city
    ).order_by("-created_at")

    context = {
        "target_profile": target_profile,
        "posts": posts,
    }
    return render(request, "pages/public_profile.html", context)


@login_required
def edit_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk, author=request.user)
    if request.method == "POST":
        content = request.POST.get("content", "").strip()
        if content:
            comment.content = content
            comment.save()
            messages.success(request, "Comment updated successfully.")
        else:
            messages.error(request, "Comment cannot be empty.")
    return redirect("post_detail", pk=comment.post.pk)

@login_required
def delete_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk, author=request.user)
    post_pk = comment.post.pk
    if request.method == "POST":
        comment.delete()
        messages.success(request, "Comment deleted successfully.")
    return redirect("post_detail", pk=post_pk)