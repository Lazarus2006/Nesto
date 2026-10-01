from django.contrib import messages
from .models import Post, Category, Entity , City
from django.shortcuts import render, redirect, get_object_or_404
from .forms import PostForm
import json
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch

@login_required
def home(request):
    profile = request.user.profile
    if not profile.city:
        return redirect("choose_city")
    
    city = profile.city
    posts = (
        Post.objects
        .filter(city = city)
        .select_related("author", "category", "entity")
        .order_by("-created_at"))
    categories = (
        Category.objects
        .filter(
            city = city.name,
            is_approved = True,
        )
        .prefetch_related("entities")
    )

    context = {
        "posts": posts,
        "categories": categories,
        "city": city,
    }

    return render(
        request,
        "pages/home.html",
        context
    )


@login_required
def entity_detail(request, pk):
    city = request.user.profile.city
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
    profile = request.user.profile
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
                    'attributes': ent.attributes or {}
                }
                for ent in cat.entities.filter(is_approved=True)
            ]
        }

    context = {
        'categories': categories,
        'categories_json': json.dumps(categories_json),
    }
    return render(request, 'pages/create_post.html', context)


@login_required
def choose_city(request):
    cities = City.objects.all().order_by("name")
    if request.method == "POST":
        city_id = request.POST.get("city")
        city = get_object_or_404(City,id=city_id)

        request.user.profile.city = city
        request.user.profile.save(update_fields=["city"])

        return redirect("home")

    return render(request, "pages/choose_city.html", {
        "cities": cities,
    })