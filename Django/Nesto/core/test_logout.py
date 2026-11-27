from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse


class LogoutMethodTests(TestCase):
    def test_auth_pages_render_without_a_configured_social_app(self):
        login_response = self.client.get(reverse("login"))
        signup_response = self.client.get(reverse("signup"))

        self.assertEqual(login_response.status_code, 200)
        self.assertEqual(signup_response.status_code, 200)
        self.assertNotContains(login_response, "Continue with Google")
        self.assertNotContains(signup_response, "Continue with Google")
        self.assertContains(login_response, "Log in")

    @override_settings(SOCIALACCOUNT_PROVIDERS={
        "google": {
            "APP": {
                "client_id": "test-client-id",
                "secret": "test-client-secret",
                "key": "",
            },
            "SCOPE": ["profile", "email"],
        }
    })
    def test_google_sign_in_is_shown_when_oauth_is_configured(self):
        login_response = self.client.get(reverse("login"))
        signup_response = self.client.get(reverse("signup"))

        self.assertContains(login_response, "Continue with Google")
        self.assertContains(signup_response, "Continue with Google")

    @override_settings(
        SOCIALACCOUNT_LOGIN_ON_GET=True,
        SOCIALACCOUNT_PROVIDERS={
            "google": {
                "APP": {
                    "client_id": "test-client-id.apps.googleusercontent.com",
                    "secret": "test-client-secret",
                    "key": "",
                },
                "SCOPE": ["profile", "email"],
            }
        },
    )
    def test_google_button_redirects_directly_to_google_with_configured_client(self):
        response = self.client.get(reverse("google_login"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("accounts.google.com", response["Location"])
        self.assertIn(
            "test-client-id.apps.googleusercontent.com",
            response["Location"],
        )

    def test_logout_requires_post(self):
        user = User.objects.create_user(username="logout-user")
        self.client.force_login(user)

        response = self.client.get(reverse("logout"))

        self.assertEqual(response.status_code, 405)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_post_logout_ends_session(self):
        user = User.objects.create_user(username="logout-user")
        self.client.force_login(user)

        response = self.client.post(reverse("logout"))

        self.assertRedirects(response, reverse("login"))
        self.assertNotIn("_auth_user_id", self.client.session)
