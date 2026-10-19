from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from .models import City, Profile


class MissingProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="profileless-user", password="test-password")
        self.client.force_login(self.user)

    def test_home_creates_profile_and_redirects_to_city_selection(self):
        response = self.client.get(reverse("home"))

        self.assertRedirects(response, reverse("choose_city"))
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(profile.display_name, self.user.username)
        self.assertIsNone(profile.city)

    def test_home_renders_after_creating_missing_profile_and_selecting_city(self):
        city = City.objects.create(name="Profile render test city", slug="profile-render-test-city")

        self.client.post(reverse("choose_city"), {"city": city.pk})
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'aria-label="Your profile"')
        self.assertEqual(Profile.objects.get(user=self.user).city, city)

    def test_city_selection_saves_city_for_user_without_profile(self):
        city = City.objects.create(name="Profileless test city", slug="profileless-test-city")

        response = self.client.post(reverse("choose_city"), {"city": city.pk})

        self.assertRedirects(response, reverse("home"))
        self.assertEqual(Profile.objects.get(user=self.user).city, city)
