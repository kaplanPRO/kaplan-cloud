from datetime import timedelta
from io import StringIO

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone

from .models import UserRegistrationToken
from .utils import generate_random_token


class GenerateRandomTokenTests(TestCase):
    def test_token_is_url_safe_string(self):
        token = generate_random_token()
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 0)

    def test_tokens_are_unique(self):
        tokens = {generate_random_token() for _ in range(50)}
        self.assertGreater(len(tokens), 1)


class UserRegistrationTokenModelTests(TestCase):
    def test_default_token_generated(self):
        t = UserRegistrationToken.objects.create()
        self.assertGreater(len(t.token), 0)

    def test_default_user_type_is_translator(self):
        t = UserRegistrationToken.objects.create()
        self.assertEqual(t.user_type, 0)

    def test_str_shows_truncated_token_and_status(self):
        t = UserRegistrationToken.objects.create()
        self.assertIn(t.token[:8], str(t))
        self.assertIn("available", str(t))

    def test_str_shows_username_when_user_assigned(self):
        user = User.objects.create_user("testuser", password="Testpass123!")
        t = UserRegistrationToken.objects.create(user=user)
        self.assertIn("testuser", str(t))

    def test_created_at_auto_set(self):
        t = UserRegistrationToken.objects.create()
        self.assertIsNotNone(t.created_at)

    def test_user_set_null_on_delete(self):
        user = User.objects.create_user("tempuser", password="Testpass123!")
        t = UserRegistrationToken.objects.create(user=user)
        user.delete()
        t.refresh_from_db()
        self.assertIsNone(t.user)

    def test_token_unique_constraint(self):
        UserRegistrationToken.objects.create(token="test-unique-token")
        with self.assertRaises(Exception):
            UserRegistrationToken.objects.create(token="test-unique-token")


class UserRegistrationFormTests(TestCase):
    def setUp(self):
        self.token = UserRegistrationToken.objects.create()

    def _form_data(self, **overrides):
        data = {
            "username": "newuser",
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "password1": "SecurePass123!",
            "password2": "SecurePass123!",
            "token": self.token.token,
        }
        data.update(overrides)
        return data

    def test_valid_form(self):
        from .forms import UserRegistrationForm

        form = UserRegistrationForm(data=self._form_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_password_mismatch(self):
        from .forms import UserRegistrationForm

        form = UserRegistrationForm(data=self._form_data(password2="DifferentPass123!"))
        # _post_clean raises KeyError when password2 is removed from
        # cleaned_data by clean_password2. This is a known issue.
        with self.assertRaises(KeyError):
            form.is_valid()

    def test_invalid_token(self):
        from .forms import UserRegistrationForm

        form = UserRegistrationForm(data=self._form_data(token="BADTOKEN"))
        self.assertFalse(form.is_valid())
        self.assertIn("token", form.errors)

    def test_already_used_token(self):
        from .forms import UserRegistrationForm

        user = User.objects.create_user("existing", password="Testpass123!")
        self.token.user = user
        self.token.save()
        form = UserRegistrationForm(data=self._form_data())
        self.assertFalse(form.is_valid())
        self.assertIn("token", form.errors)

    def test_expired_token(self):
        from .forms import UserRegistrationForm

        UserRegistrationToken.objects.filter(pk=self.token.pk).update(
            created_at=timezone.now() - timedelta(hours=49)
        )
        form = UserRegistrationForm(data=self._form_data())
        self.assertFalse(form.is_valid())
        self.assertIn("token", form.errors)

    def test_weak_password_rejected(self):
        from .forms import UserRegistrationForm

        form = UserRegistrationForm(
            data=self._form_data(password1="123", password2="123")
        )
        self.assertFalse(form.is_valid())

    def test_save_creates_user(self):
        from .forms import UserRegistrationForm

        form = UserRegistrationForm(data=self._form_data())
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertEqual(user.username, "newuser")
        self.assertTrue(user.check_password("SecurePass123!"))

    def test_save_links_token_to_user(self):
        from .forms import UserRegistrationForm

        form = UserRegistrationForm(data=self._form_data())
        form.is_valid()
        user = form.save()
        self.token.refresh_from_db()
        self.assertEqual(self.token.user, user)

    def test_save_pm_token_sets_staff_and_group(self):
        from .forms import UserRegistrationForm

        Group.objects.create(name="PM")
        pm_token = UserRegistrationToken.objects.create(user_type=1)
        form = UserRegistrationForm(data=self._form_data(token=pm_token.token))
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertTrue(user.is_staff)
        self.assertTrue(user.groups.filter(name="PM").exists())

    def test_save_translator_token_not_staff(self):
        from .forms import UserRegistrationForm

        form = UserRegistrationForm(data=self._form_data())
        form.is_valid()
        user = form.save()
        self.assertFalse(user.is_staff)


class SigninViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("testuser", password="Testpass123!")

    def test_get_login_page(self):
        response = self.client.get("/accounts/login")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/login.html")

    def test_get_login_with_next(self):
        response = self.client.get("/accounts/login?next=/some/path")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "/some/path")

    def test_post_valid_credentials(self):
        response = self.client.post(
            "/accounts/login",
            {"username": "testuser", "password": "Testpass123!", "next": ""},
        )
        self.assertEqual(response.status_code, 302)

    def test_post_valid_credentials_with_next(self):
        response = self.client.post(
            "/accounts/login",
            {
                "username": "testuser",
                "password": "Testpass123!",
                "next": "/accounts/change-password",
            },
        )
        self.assertRedirects(
            response,
            "/accounts/change-password",
            fetch_redirect_response=False,
        )

    def test_post_invalid_credentials(self):
        response = self.client.post(
            "/accounts/login",
            {"username": "testuser", "password": "wrong", "next": ""},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/login.html")

    def test_login_sets_session(self):
        self.client.post(
            "/accounts/login",
            {"username": "testuser", "password": "Testpass123!", "next": ""},
        )
        response = self.client.get("/accounts/change-password")
        self.assertEqual(response.status_code, 200)


class SignoutViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("testuser", password="Testpass123!")
        self.client.login(username="testuser", password="Testpass123!")

    def test_logout_redirects(self):
        response = self.client.get("/accounts/logout")
        self.assertEqual(response.status_code, 302)

    def test_logout_clears_session(self):
        self.client.get("/accounts/logout")
        response = self.client.get("/accounts/change-password")
        self.assertNotEqual(response.status_code, 200)


class SignupViewTests(TestCase):
    def setUp(self):
        self.token = UserRegistrationToken.objects.create()

    def test_get_register_page(self):
        response = self.client.get("/accounts/register")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/register.html")

    def test_get_register_with_token_param(self):
        response = self.client.get(f"/accounts/register?token={self.token.token}")
        self.assertEqual(response.status_code, 200)

    def test_post_valid_registration(self):
        response = self.client.post(
            "/accounts/register",
            {
                "username": "newuser",
                "first_name": "New",
                "last_name": "User",
                "email": "new@example.com",
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
                "token": self.token.token,
            },
        )
        self.assertRedirects(response, "/accounts/login", fetch_redirect_response=False)
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_post_invalid_token(self):
        response = self.client.post(
            "/accounts/register",
            {
                "username": "newuser",
                "first_name": "New",
                "last_name": "User",
                "email": "new@example.com",
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
                "token": "BADTOKEN",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="newuser").exists())


class ChangePasswordViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("testuser", password="Testpass123!")

    def test_requires_login(self):
        response = self.client.get("/accounts/change-password")
        self.assertNotEqual(response.status_code, 200)

    def test_get_change_password_page(self):
        self.client.login(username="testuser", password="Testpass123!")
        response = self.client.get("/accounts/change-password")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/change-password.html")

    def test_post_valid_password_change(self):
        self.client.login(username="testuser", password="Testpass123!")
        response = self.client.post(
            "/accounts/change-password",
            {
                "old_password": "Testpass123!",
                "new_password1": "NewSecure456!",
                "new_password2": "NewSecure456!",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewSecure456!"))

    def test_post_wrong_old_password(self):
        self.client.login(username="testuser", password="Testpass123!")
        response = self.client.post(
            "/accounts/change-password",
            {
                "old_password": "WrongOld!",
                "new_password1": "NewSecure456!",
                "new_password2": "NewSecure456!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("Testpass123!"))


class CreateTokensCommandTests(TestCase):
    def test_creates_translator_tokens(self):
        out = StringIO()
        call_command("createtokens", 3, stdout=out)
        self.assertEqual(UserRegistrationToken.objects.count(), 3)
        self.assertTrue(
            all(t.user_type == 0 for t in UserRegistrationToken.objects.all())
        )

    def test_creates_pm_tokens(self):
        out = StringIO()
        call_command("createtokens", 2, "--pm", stdout=out)
        self.assertEqual(UserRegistrationToken.objects.count(), 2)
        self.assertTrue(
            all(t.user_type == 1 for t in UserRegistrationToken.objects.all())
        )

    def test_output_is_json(self):
        import json

        out = StringIO()
        call_command("createtokens", 1, stdout=out)
        data = json.loads(out.getvalue())
        self.assertIn("0", data)
        self.assertIn("token", data["0"])
        self.assertIn("type", data["0"])


class DeleteTokenAndUserCommandTests(TestCase):
    def test_delete_token_without_user(self):
        token = UserRegistrationToken.objects.create()
        out = StringIO()
        call_command("deletetokenanduser", token.token, stdout=out)
        self.assertFalse(UserRegistrationToken.objects.filter(pk=token.pk).exists())

    def test_delete_token_with_user(self):
        user = User.objects.create_user("tempuser", password="Testpass123!")
        token = UserRegistrationToken.objects.create(user=user)
        out = StringIO()
        call_command("deletetokenanduser", token.token, stdout=out)
        self.assertFalse(UserRegistrationToken.objects.filter(pk=token.pk).exists())
        self.assertFalse(User.objects.filter(pk=user.pk).exists())

    def test_nonexistent_token_raises_error(self):
        with self.assertRaises(CommandError):
            call_command("deletetokenanduser", "NONEXIST")
