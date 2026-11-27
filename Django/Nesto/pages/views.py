from django.contrib import messages
from django.core.exceptions import PermissionDenied
from .models import (
    Post,
    Category,
    Entity,
    City,
    Comment,
    Profile,
    ServiceMessage,
    ServiceRequest,
    ServiceResponse,
    get_or_create_profile,
)
from django.shortcuts import render, redirect, get_object_or_404
from .forms import CommentForm
import json
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.contrib.auth.models import User
from django.conf import settings
from django.views.decorators.http import require_POST
from django.db import IntegrityError
from .forms import ServiceRequestForm, ServiceResponseForm, ServiceMessageForm

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
        "mapbox_token": settings.MAPBOX_TOKEN,
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
        'mapbox_token': settings.MAPBOX_TOKEN,
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
@require_POST
def add_comment(request, pk):
    post = get_object_or_404(Post, pk=pk)

    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            parent_id = request.POST.get("parent_id")
            if parent_id:
                comment.parent = get_object_or_404(Comment, pk=parent_id, post=post)
            comment.save()
            messages.success(request, "Reply added!" if comment.parent_id else "Comment added!")
        else:
            messages.error(request, "Please enter a valid comment.")

    return redirect("post_detail", pk=post.pk)


@login_required
def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    all_comments = list(post.comments.select_related("author").order_by("created_at"))
    comments_by_parent = {}
    for comment in all_comments:
        comments_by_parent.setdefault(comment.parent_id, []).append(comment)
    for comment in all_comments:
        comment.thread_replies = comments_by_parent.get(comment.pk, [])

    return render(request, "pages/post_detail.html", {
        "post": post,
        "comments": comments_by_parent.get(None, []),
        "comment_count": len(all_comments),
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
@require_POST
def edit_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk, author=request.user)
    form = CommentForm(request.POST, instance=comment)
    if form.is_valid():
        form.save()
        messages.success(request, "Comment updated successfully.")
    else:
        messages.error(request, "Please enter a valid comment.")
    return redirect("post_detail", pk=comment.post.pk)


@login_required
@require_POST
def delete_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk, author=request.user)
    post_pk = comment.post.pk
    comment.delete()
    messages.success(request, "Comment deleted successfully.")
    return redirect("post_detail", pk=post_pk)


def _service_city_or_redirect(request):
    city = get_or_create_profile(request.user).city
    return city, None if city else redirect("choose_city")


@login_required
def service_list(request):
    city, response = _service_city_or_redirect(request)
    if response:
        return response
    service_requests = (
        ServiceRequest.objects.filter(city=city)
        .select_related("requester", "accepted_response")
        .prefetch_related("responses")
    )
    return render(request, "pages/service_list.html", {
        "city": city,
        "service_requests": service_requests,
    })


@login_required
def service_create(request):
    city, response = _service_city_or_redirect(request)
    if response:
        return response
    form = ServiceRequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        service_request = form.save(commit=False)
        service_request.city = city
        service_request.requester = request.user
        service_request.save()
        messages.success(request, "Your service request is now posted.")
        return redirect("service_detail", pk=service_request.pk)
    return render(request, "pages/service_create.html", {"form": form, "city": city})


@login_required
def service_detail(request, pk):
    city, response = _service_city_or_redirect(request)
    if response:
        return response
    service_request = get_object_or_404(
        ServiceRequest.objects.select_related("requester", "accepted_response__responder"),
        pk=pk,
        city=city,
    )
    responses = service_request.responses.select_related("responder").all()
    accepted_response = service_request.accepted_response
    can_message = bool(
        accepted_response
        and request.user in (service_request.requester, accepted_response.responder)
    )
    other_participant = (
        accepted_response.responder
        if accepted_response and request.user == service_request.requester
        else service_request.requester
    )
    messages_qs = (
        service_request.messages.select_related("sender").all()
        if can_message else ServiceMessage.objects.none()
    )
    return render(request, "pages/service_detail.html", {
        "service_request": service_request,
        "responses": responses,
        "response_form": ServiceResponseForm(),
        "message_form": ServiceMessageForm(),
        "messages_thread": messages_qs,
        "can_message": can_message,
        "other_participant": other_participant,
        "is_requester": request.user == service_request.requester,
    })


@login_required
@require_POST
def service_respond(request, pk):
    city, redirect_response = _service_city_or_redirect(request)
    if redirect_response:
        return redirect_response
    with transaction.atomic():
        service_request = get_object_or_404(
            ServiceRequest.objects.select_for_update(),
            pk=pk,
            city=city,
        )
        if service_request.status != ServiceRequest.Status.OPEN:
            messages.error(request, "This service request is no longer accepting responses.")
        elif service_request.requester_id == request.user.id:
            messages.error(request, "You cannot respond to your own service request.")
        else:
            form = ServiceResponseForm(request.POST)
            if form.is_valid():
                service_response = form.save(commit=False)
                service_response.service_request = service_request
                service_response.responder = request.user
                try:
                    with transaction.atomic():
                        if ServiceResponse.objects.filter(
                            service_request=service_request,
                            responder=request.user,
                            kind=service_response.kind,
                        ).exists():
                            raise IntegrityError
                        service_response.save()
                except IntegrityError:
                    messages.error(request, "You have already sent a response of this type.")
                else:
                    messages.success(request, "Your response has been sent.")
            else:
                messages.error(request, "Please enter a valid response.")
    return redirect("service_detail", pk=service_request.pk)


@login_required
@require_POST
def service_accept(request, pk, response_pk):
    city, redirect_response = _service_city_or_redirect(request)
    if redirect_response:
        return redirect_response
    with transaction.atomic():
        service_request = get_object_or_404(
            ServiceRequest.objects.select_for_update(),
            pk=pk,
            city=city,
            requester=request.user,
        )
        if service_request.status != ServiceRequest.Status.OPEN:
            messages.error(request, "This request is not open for accepting offers.")
        else:
            accepted_response = get_object_or_404(
                ServiceResponse,
                pk=response_pk,
                service_request=service_request,
                kind=ServiceResponse.Kind.OFFER,
            )
            service_request.accepted_response = accepted_response
            service_request.status = ServiceRequest.Status.IN_PROGRESS
            service_request.save(update_fields=["accepted_response", "status", "updated_at"])
            messages.success(request, "Offer accepted. You can now message each other privately.")
    return redirect("service_detail", pk=pk)


@login_required
@require_POST
def service_update_status(request, pk):
    city, redirect_response = _service_city_or_redirect(request)
    if redirect_response:
        return redirect_response
    with transaction.atomic():
        service_request = get_object_or_404(
            ServiceRequest.objects.select_for_update(),
            pk=pk,
            city=city,
            requester=request.user,
        )
        new_status = request.POST.get("status")
        allowed_transitions = {
            ServiceRequest.Status.OPEN: {ServiceRequest.Status.CANCELLED},
            ServiceRequest.Status.IN_PROGRESS: {
                ServiceRequest.Status.COMPLETED,
                ServiceRequest.Status.CANCELLED,
            },
        }
        if new_status not in allowed_transitions.get(service_request.status, set()):
            messages.error(request, "That status change is not allowed.")
        else:
            service_request.status = new_status
            service_request.save(update_fields=["status", "updated_at"])
            messages.success(request, f"Request marked {service_request.get_status_display().lower()}.")
    return redirect("service_detail", pk=service_request.pk)


@login_required
@require_POST
def service_message(request, pk):
    city, redirect_response = _service_city_or_redirect(request)
    if redirect_response:
        return redirect_response
    service_request = get_object_or_404(
        ServiceRequest.objects.select_related("accepted_response__responder"),
        pk=pk,
        city=city,
    )
    accepted_response = service_request.accepted_response
    if not accepted_response or request.user not in (
        service_request.requester,
        accepted_response.responder,
    ):
        raise PermissionDenied
    form = ServiceMessageForm(request.POST)
    if form.is_valid():
        service_message_obj = form.save(commit=False)
        service_message_obj.service_request = service_request
        service_message_obj.sender = request.user
        service_message_obj.save()
        messages.success(request, "Message sent.")
    else:
        messages.error(request, "Please enter a valid message.")
    return redirect("service_detail", pk=service_request.pk)