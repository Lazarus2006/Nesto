from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import City, Comment, Post, Profile, ServiceMessage, ServiceRequest, ServiceResponse


class FeatureTestCase(TestCase):
    def setUp(self):
        self.city = City.objects.create(name="Feature City", slug="feature-city")
        self.other_city = City.objects.create(name="Other City", slug="other-city")
        self.requester = User.objects.create_user(username="requester")
        self.provider = User.objects.create_user(username="provider")
        self.bystander = User.objects.create_user(username="bystander")
        for user in (self.requester, self.provider, self.bystander):
            Profile.objects.create(user=user, city=self.city, display_name=user.username)


class CommentReplyTests(FeatureTestCase):
    def setUp(self):
        super().setUp()
        self.post = Post.objects.create(
            city=self.city,
            author=self.requester,
            title="A local question",
            content="Question details",
        )

    def test_user_can_reply_to_comment_and_thread_is_rendered(self):
        parent = Comment.objects.create(
            post=self.post,
            author=self.requester,
            content="First comment",
        )
        self.client.force_login(self.provider)

        response = self.client.post(
            reverse("add_comment", args=[self.post.pk]),
            {"content": "A useful reply", "parent_id": parent.pk},
        )

        self.assertRedirects(response, reverse("post_detail", args=[self.post.pk]))
        reply = Comment.objects.get(parent=parent)
        self.assertEqual(reply.author, self.provider)
        self.assertEqual(reply.post, self.post)
        detail = self.client.get(reverse("post_detail", args=[self.post.pk]))
        self.assertContains(detail, "A useful reply")
        self.assertContains(detail, 'name="parent_id"')
        self.assertEqual(detail.context["comment_count"], 2)

    def test_reply_parent_must_belong_to_same_post(self):
        other_post = Post.objects.create(
            city=self.city,
            author=self.requester,
            title="Another question",
            content="Other details",
        )
        parent = Comment.objects.create(
            post=other_post,
            author=self.requester,
            content="Unrelated comment",
        )
        self.client.force_login(self.provider)

        response = self.client.post(
            reverse("add_comment", args=[self.post.pk]),
            {"content": "Invalid reply", "parent_id": parent.pk},
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(Comment.objects.filter(content="Invalid reply").exists())

    def test_edit_and_delete_comments_require_post(self):
        comment = Comment.objects.create(
            post=self.post,
            author=self.requester,
            content="Original",
        )
        self.client.force_login(self.requester)

        edit_response = self.client.get(reverse("edit_comment", args=[comment.pk]))
        delete_response = self.client.get(reverse("delete_comment", args=[comment.pk]))

        self.assertEqual(edit_response.status_code, 405)
        self.assertEqual(delete_response.status_code, 405)
        self.assertTrue(Comment.objects.filter(pk=comment.pk).exists())


class ServiceRequestTests(FeatureTestCase):
    def create_request(self, requester=None, city=None, **kwargs):
        return ServiceRequest.objects.create(
            requester=requester or self.requester,
            city=city or self.city,
            title=kwargs.get("title", "Fix my laptop"),
            description=kwargs.get("description", "Looking for a local laptop repair."),
            category=kwargs.get("category", "Repairs"),
            location=kwargs.get("location", "Central area"),
            budget=kwargs.get("budget", "Under ₹1,000"),
        )

    def test_request_creation_is_scoped_to_the_requester_city(self):
        self.client.force_login(self.requester)
        response = self.client.post(
            reverse("service_create"),
            {
                "title": "Need a video edited",
                "description": "A short video for a local event.",
                "category": "Creative",
                "location": "Downtown",
                "budget": "Flexible",
            },
        )

        service_request = ServiceRequest.objects.get(title="Need a video edited")
        self.assertRedirects(response, reverse("service_detail", args=[service_request.pk]))
        self.assertEqual(service_request.city, self.city)
        self.assertEqual(service_request.requester, self.requester)

    def test_service_requests_are_not_visible_across_cities(self):
        service_request = self.create_request(city=self.other_city)
        self.client.force_login(self.provider)

        list_response = self.client.get(reverse("service_list"))
        detail_response = self.client.get(reverse("service_detail", args=[service_request.pk]))

        self.assertNotContains(list_response, service_request.title)
        self.assertEqual(detail_response.status_code, 404)

    def test_requester_cannot_respond_to_own_request(self):
        service_request = self.create_request()
        self.client.force_login(self.requester)

        response = self.client.post(
            reverse("service_respond", args=[service_request.pk]),
            {"kind": "offer", "content": "I can do it."},
        )

        self.assertRedirects(response, reverse("service_detail", args=[service_request.pk]))
        self.assertFalse(service_request.responses.exists())

    def test_offer_acceptance_opens_private_messaging_for_only_the_participants(self):
        service_request = self.create_request()
        offer = ServiceResponse.objects.create(
            service_request=service_request,
            responder=self.provider,
            kind=ServiceResponse.Kind.OFFER,
            content="I can repair laptops locally.",
        )
        self.client.force_login(self.requester)

        accept_response = self.client.post(
            reverse("service_accept", args=[service_request.pk, offer.pk])
        )

        self.assertRedirects(accept_response, reverse("service_detail", args=[service_request.pk]))
        service_request.refresh_from_db()
        self.assertEqual(service_request.status, ServiceRequest.Status.IN_PROGRESS)
        self.assertEqual(service_request.accepted_response, offer)

        self.client.force_login(self.provider)
        self.client.post(
            reverse("service_message", args=[service_request.pk]),
            {"content": "When can I bring it by?"},
        )
        self.assertTrue(ServiceMessage.objects.filter(
            service_request=service_request,
            sender=self.provider,
        ).exists())

        self.client.force_login(self.bystander)
        detail_response = self.client.get(reverse("service_detail", args=[service_request.pk]))
        message_response = self.client.post(
            reverse("service_message", args=[service_request.pk]),
            {"content": "I should not see or send this."},
        )
        self.assertNotContains(detail_response, "When can I bring it by?")
        self.assertEqual(message_response.status_code, 403)
        self.assertEqual(ServiceMessage.objects.filter(service_request=service_request).count(), 1)

    def test_only_requester_can_accept_an_offer_and_suggestions_are_not_acceptable(self):
        service_request = self.create_request()
        suggestion = ServiceResponse.objects.create(
            service_request=service_request,
            responder=self.provider,
            kind=ServiceResponse.Kind.SUGGESTION,
            content="Try the repair shop near the market.",
        )
        self.client.force_login(self.bystander)
        non_owner_response = self.client.post(
            reverse("service_accept", args=[service_request.pk, suggestion.pk])
        )
        self.assertEqual(non_owner_response.status_code, 404)

        self.client.force_login(self.requester)
        suggestion_response = self.client.post(
            reverse("service_accept", args=[service_request.pk, suggestion.pk])
        )
        self.assertEqual(suggestion_response.status_code, 404)
        service_request.refresh_from_db()
        self.assertEqual(service_request.status, ServiceRequest.Status.OPEN)
        self.assertIsNone(service_request.accepted_response)

    def test_only_requester_can_change_request_status(self):
        service_request = self.create_request()
        self.client.force_login(self.provider)
        forbidden = self.client.post(
            reverse("service_update_status", args=[service_request.pk]),
            {"status": ServiceRequest.Status.CANCELLED},
        )
        self.assertEqual(forbidden.status_code, 404)

        self.client.force_login(self.requester)
        completed_while_open = self.client.post(
            reverse("service_update_status", args=[service_request.pk]),
            {"status": ServiceRequest.Status.COMPLETED},
        )
        self.assertRedirects(
            completed_while_open,
            reverse("service_detail", args=[service_request.pk]),
        )
        service_request.refresh_from_db()
        self.assertEqual(service_request.status, ServiceRequest.Status.OPEN)

    def test_response_types_are_unique_per_user(self):
        service_request = self.create_request()
        self.client.force_login(self.provider)
        url = reverse("service_respond", args=[service_request.pk])
        data = {"kind": "suggestion", "content": "Try the nearby repair shop."}

        first = self.client.post(url, data)
        second = self.client.post(url, data)

        self.assertRedirects(first, reverse("service_detail", args=[service_request.pk]))
        self.assertRedirects(second, reverse("service_detail", args=[service_request.pk]))
        self.assertEqual(service_request.responses.filter(
            responder=self.provider,
            kind=ServiceResponse.Kind.SUGGESTION,
        ).count(), 1)
