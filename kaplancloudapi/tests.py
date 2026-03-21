from unittest import mock

from django.contrib.auth.models import Group, User
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from kaplancloudapp.models import (
    Client,
    LanguageProfile,
    Project,
    ProjectFile,
    ProjectReferenceFile,
    TranslationMemory,
)
from kaplancloudapi.models import ProjectFileWebHook, ProjectWebHook


class APITestBase(TestCase):
    """Base class providing common fixtures for API tests."""

    @mock.patch("kaplancloudapp.models.Path.mkdir", mock.MagicMock())
    def setUp(self):
        self.admin_user = User.objects.create_user(
            "admin", password="Testpass123!", is_staff=True
        )
        self.regular_user = User.objects.create_user(
            "regular", password="Testpass123!", is_staff=False
        )

        self.source_lang = LanguageProfile.objects.create(
            name="English", iso_code="en", created_by=self.admin_user
        )
        self.target_lang = LanguageProfile.objects.create(
            name="French", iso_code="fr", created_by=self.admin_user
        )

        self.client_obj = Client.objects.create(name="Acme")

        self.api_client = APIClient()
        self.api_client.force_authenticate(user=self.admin_user)

    def _create_project(self, **kwargs):
        defaults = {
            "name": "Test Project",
            "source_language": self.source_lang,
            "target_language": self.target_lang,
            "created_by": self.admin_user,
            "directory": "test-project",
        }
        defaults.update(kwargs)
        return Project.objects.create(**defaults)


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class ClientViewSetTests(APITestBase):
    def test_list_clients(self):
        response = self.api_client.get("/api/clients/")
        self.assertEqual(response.status_code, 200)

    def test_create_client(self):
        response = self.api_client.post(
            "/api/clients/", {"name": "NewClient", "team": []}
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["name"], "NewClient")

    def test_retrieve_client(self):
        response = self.api_client.get(f"/api/clients/{self.client_obj.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Acme")

    def test_update_client(self):
        response = self.api_client.put(
            f"/api/clients/{self.client_obj.id}/",
            {"name": "Acme Corp", "team": []},
        )
        self.assertEqual(response.status_code, 200)
        self.client_obj.refresh_from_db()
        self.assertEqual(self.client_obj.name, "Acme Corp")

    def test_partial_update_client(self):
        response = self.api_client.patch(
            f"/api/clients/{self.client_obj.id}/",
            {"name": "Acme Inc"},
        )
        self.assertEqual(response.status_code, 200)
        self.client_obj.refresh_from_db()
        self.assertEqual(self.client_obj.name, "Acme Inc")

    def test_delete_client(self):
        response = self.api_client.delete(f"/api/clients/{self.client_obj.id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Client.objects.filter(id=self.client_obj.id).exists())

    def test_filter_by_name(self):
        Client.objects.create(name="Other")
        response = self.api_client.get("/api/clients/?name=Acme")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], "Acme")

    def test_filter_by_team_member_username(self):
        self.client_obj.team.add(self.admin_user)
        response = self.api_client.get("/api/clients/?team_member_username=admin")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)

    def test_filter_by_name_no_match(self):
        response = self.api_client.get("/api/clients/?name=Nonexistent")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 0)


# ---------------------------------------------------------------------------
# Group
# ---------------------------------------------------------------------------


class GroupViewSetTests(APITestBase):
    def test_list_groups(self):
        response = self.api_client.get("/api/groups/")
        self.assertEqual(response.status_code, 200)

    def test_create_group(self):
        response = self.api_client.post("/api/groups/", {"name": "Translators"})
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Group.objects.filter(name="Translators").exists())

    def test_retrieve_group(self):
        group = Group.objects.create(name="Reviewers")
        response = self.api_client.get(f"/api/groups/{group.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Reviewers")

    def test_update_group(self):
        group = Group.objects.create(name="Old")
        response = self.api_client.put(f"/api/groups/{group.id}/", {"name": "New"})
        self.assertEqual(response.status_code, 200)
        group.refresh_from_db()
        self.assertEqual(group.name, "New")

    def test_delete_group(self):
        group = Group.objects.create(name="ToDelete")
        response = self.api_client.delete(f"/api/groups/{group.id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Group.objects.filter(id=group.id).exists())


# ---------------------------------------------------------------------------
# LanguageProfile
# ---------------------------------------------------------------------------


class LanguageProfileViewSetTests(APITestBase):
    def test_list_language_profiles(self):
        response = self.api_client.get("/api/language-profiles/")
        self.assertEqual(response.status_code, 200)

    def test_list_ordered_by_iso_code(self):
        response = self.api_client.get("/api/language-profiles/")
        iso_codes = [r["iso_code"] for r in response.data["results"]]
        self.assertEqual(iso_codes, sorted(iso_codes))

    def test_create_language_profile(self):
        response = self.api_client.post(
            "/api/language-profiles/",
            {"name": "German", "iso_code": "de", "is_ltr": True},
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(LanguageProfile.objects.filter(iso_code="de").exists())

    def test_create_sets_created_by(self):
        self.api_client.post(
            "/api/language-profiles/",
            {"name": "Spanish", "iso_code": "es"},
        )
        lp = LanguageProfile.objects.get(iso_code="es")
        self.assertEqual(lp.created_by, self.admin_user)

    def test_create_default_is_ltr_true(self):
        self.api_client.post(
            "/api/language-profiles/",
            {"name": "Italian", "iso_code": "it"},
        )
        lp = LanguageProfile.objects.get(iso_code="it")
        self.assertTrue(lp.is_ltr)

    def test_retrieve_language_profile(self):
        response = self.api_client.get("/api/language-profiles/en/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "English")

    def test_update_language_profile(self):
        response = self.api_client.put(
            "/api/language-profiles/en/",
            {"name": "English (US)", "iso_code": "en", "is_ltr": True},
        )
        self.assertEqual(response.status_code, 200)
        self.source_lang.refresh_from_db()
        self.assertEqual(self.source_lang.name, "English (US)")

    def test_delete_language_profile(self):
        lp = LanguageProfile.objects.create(
            name="Japanese", iso_code="ja", created_by=self.admin_user
        )
        response = self.api_client.delete(f"/api/language-profiles/{lp.iso_code}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(LanguageProfile.objects.filter(iso_code="ja").exists())


# ---------------------------------------------------------------------------
# Project
# ---------------------------------------------------------------------------


class ProjectViewSetTests(APITestBase):
    def test_list_projects(self):
        self._create_project()
        response = self.api_client.get("/api/projects/")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data["results"]), 1)

    def test_create_project(self):
        response = self.api_client.post(
            "/api/projects/",
            {
                "name": "New Project",
                "source_language": "en",
                "target_language": "fr",
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["name"], "New Project")

    def test_create_sets_created_by(self):
        self.api_client.post(
            "/api/projects/",
            {
                "name": "Created By Test",
                "source_language": "en",
                "target_language": "fr",
            },
        )
        project = Project.objects.get(name="Created By Test")
        self.assertEqual(project.created_by, self.admin_user)

    def test_create_default_status_zero(self):
        response = self.api_client.post(
            "/api/projects/",
            {
                "name": "Status Test",
                "source_language": "en",
                "target_language": "fr",
            },
        )
        self.assertEqual(response.data["status"], 0)

    def test_retrieve_project(self):
        project = self._create_project()
        response = self.api_client.get(f"/api/projects/{project.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Test Project")
        self.assertIn("uuid", response.data)

    def test_update_project(self):
        project = self._create_project()
        response = self.api_client.patch(
            f"/api/projects/{project.id}/",
            {"name": "Updated Project"},
        )
        self.assertEqual(response.status_code, 200)
        project.refresh_from_db()
        self.assertEqual(project.name, "Updated Project")

    @mock.patch("kaplancloudapp.models.shutil.rmtree")
    def test_delete_project(self, mock_rmtree):
        project = self._create_project()
        response = self.api_client.delete(f"/api/projects/{project.id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Project.objects.filter(id=project.id).exists())

    def test_filter_by_client_name(self):
        self._create_project(client=self.client_obj, name="P1")
        self._create_project(name="P2")
        response = self.api_client.get("/api/projects/?client_name=Acme")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], "P1")

    def test_filter_by_source_language(self):
        self._create_project()
        response = self.api_client.get("/api/projects/?source_language=en")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data["results"]), 1)

    def test_filter_by_target_language(self):
        self._create_project()
        response = self.api_client.get("/api/projects/?target_language=fr")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data["results"]), 1)

    def test_serializer_fields(self):
        project = self._create_project()
        response = self.api_client.get(f"/api/projects/{project.id}/")
        expected_fields = {
            "id",
            "uuid",
            "name",
            "source_language",
            "target_language",
            "client",
            "managed_by",
            "status",
            "translationmemories",
            "due_by",
            "_are_all_files_submitted",
        }
        self.assertEqual(set(response.data.keys()), expected_fields)


# ---------------------------------------------------------------------------
# ProjectWebHook
# ---------------------------------------------------------------------------


class ProjectWebHookViewSetTests(APITestBase):
    def setUp(self):
        super().setUp()
        self.project = self._create_project()

    def test_list_webhooks(self):
        response = self.api_client.get("/api/project-webhooks/")
        self.assertEqual(response.status_code, 200)

    @mock.patch("kaplancloudapi.models.requests.post")
    def test_create_webhook(self, mock_post):
        response = self.api_client.post(
            "/api/project-webhooks/",
            {
                "target": "https://example.com/hook",
                "header": {},
                "project": self.project.id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)

    @mock.patch("kaplancloudapi.models.requests.post")
    def test_retrieve_webhook(self, mock_post):
        webhook = ProjectWebHook.objects.create(
            target="https://example.com/hook",
            header={},
            project=self.project,
        )
        response = self.api_client.get(f"/api/project-webhooks/{webhook.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["target"], "https://example.com/hook")

    @mock.patch("kaplancloudapi.models.requests.post")
    def test_update_webhook(self, mock_post):
        webhook = ProjectWebHook.objects.create(
            target="https://example.com/hook",
            header={},
            project=self.project,
        )
        response = self.api_client.patch(
            f"/api/project-webhooks/{webhook.id}/",
            {"target": "https://example.com/new-hook"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        webhook.refresh_from_db()
        self.assertEqual(webhook.target, "https://example.com/new-hook")

    @mock.patch("kaplancloudapi.models.requests.post")
    def test_delete_webhook(self, mock_post):
        webhook = ProjectWebHook.objects.create(
            target="https://example.com/hook",
            header={},
            project=self.project,
        )
        response = self.api_client.delete(f"/api/project-webhooks/{webhook.id}/")
        self.assertEqual(response.status_code, 204)


# ---------------------------------------------------------------------------
# ProjectFile
# ---------------------------------------------------------------------------


@mock.patch("kaplancloudapp.models.NewFileThread")
class ProjectFileViewSetTests(APITestBase):
    def setUp(self):
        super().setUp()
        self.project = self._create_project()

    def test_list_project_files(self, mock_thread):
        response = self.api_client.get("/api/project-files/")
        self.assertEqual(response.status_code, 200)

    def test_create_project_file(self, mock_thread):
        response = self.api_client.post(
            "/api/project-files/",
            {"name": "test.xlf", "project": self.project.id, "status": 0},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["name"], "test.xlf")

    def test_retrieve_excludes_source_and_bilingual(self, mock_thread):
        pf = ProjectFile.objects.create(name="test.xlf", project=self.project, status=0)
        response = self.api_client.get(f"/api/project-files/{pf.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("source_file", response.data)
        self.assertNotIn("bilingual_file", response.data)

    def test_update_project_file(self, mock_thread):
        pf = ProjectFile.objects.create(name="test.xlf", project=self.project, status=0)
        response = self.api_client.patch(
            f"/api/project-files/{pf.id}/",
            {"name": "renamed.xlf"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        pf.refresh_from_db()
        self.assertEqual(pf.name, "renamed.xlf")

    def test_delete_project_file(self, mock_thread):
        pf = ProjectFile.objects.create(name="test.xlf", project=self.project, status=0)
        response = self.api_client.delete(f"/api/project-files/{pf.id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(ProjectFile.objects.filter(id=pf.id).exists())

    def test_filter_by_project_id(self, mock_thread):
        other_project = self._create_project(name="Other")
        ProjectFile.objects.create(name="a.xlf", project=self.project, status=0)
        ProjectFile.objects.create(name="b.xlf", project=other_project, status=0)
        response = self.api_client.get(
            f"/api/project-files/?project_id={self.project.id}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], "a.xlf")

    def test_default_status_zero(self, mock_thread):
        response = self.api_client.post(
            "/api/project-files/",
            {"name": "test.xlf", "project": self.project.id},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], 0)


# ---------------------------------------------------------------------------
# ProjectFileWebHook
# ---------------------------------------------------------------------------


class ProjectFileWebHookViewSetTests(APITestBase):
    @mock.patch("kaplancloudapp.models.NewFileThread")
    def setUp(self, mock_thread):
        super().setUp()
        self.project = self._create_project()
        self.project_file = ProjectFile.objects.create(
            name="test.xlf", project=self.project, status=0
        )

    def test_list_webhooks(self):
        response = self.api_client.get("/api/project-file-webhooks/")
        self.assertEqual(response.status_code, 200)

    @mock.patch("kaplancloudapi.models.requests.post")
    def test_create_webhook(self, mock_post):
        response = self.api_client.post(
            "/api/project-file-webhooks/",
            {
                "target": "https://example.com/hook",
                "header": {},
                "project_file": self.project_file.id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)

    @mock.patch("kaplancloudapi.models.requests.post")
    def test_retrieve_webhook(self, mock_post):
        webhook = ProjectFileWebHook.objects.create(
            target="https://example.com/hook",
            header={},
            project_file=self.project_file,
        )
        response = self.api_client.get(f"/api/project-file-webhooks/{webhook.id}/")
        self.assertEqual(response.status_code, 200)

    @mock.patch("kaplancloudapi.models.requests.post")
    def test_delete_webhook(self, mock_post):
        webhook = ProjectFileWebHook.objects.create(
            target="https://example.com/hook",
            header={},
            project_file=self.project_file,
        )
        response = self.api_client.delete(f"/api/project-file-webhooks/{webhook.id}/")
        self.assertEqual(response.status_code, 204)


# ---------------------------------------------------------------------------
# ProjectReferenceFile
# ---------------------------------------------------------------------------


class ProjectReferenceFileViewSetTests(APITestBase):
    def setUp(self):
        super().setUp()
        self.project = self._create_project()

    def test_list_reference_files(self):
        response = self.api_client.get("/api/project-reference-files/")
        self.assertEqual(response.status_code, 200)

    def test_retrieve_reference_file(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        ref_file = SimpleUploadedFile("ref.txt", b"reference content")
        prf = ProjectReferenceFile.objects.create(
            name="ref.txt",
            project=self.project,
            reference_file=ref_file,
        )
        response = self.api_client.get(f"/api/project-reference-files/{prf.id}/")
        self.assertEqual(response.status_code, 200)
        expected_fields = {"id", "uuid", "name", "reference_file", "project"}
        self.assertEqual(set(response.data.keys()), expected_fields)

    def test_delete_reference_file(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        ref_file = SimpleUploadedFile("ref.txt", b"reference content")
        prf = ProjectReferenceFile.objects.create(
            name="ref.txt",
            project=self.project,
            reference_file=ref_file,
        )
        response = self.api_client.delete(f"/api/project-reference-files/{prf.id}/")
        self.assertEqual(response.status_code, 204)


# ---------------------------------------------------------------------------
# TranslationMemory
# ---------------------------------------------------------------------------


class TranslationMemoryViewSetTests(APITestBase):
    def test_list_translation_memories(self):
        response = self.api_client.get("/api/translation-memories/")
        self.assertEqual(response.status_code, 200)

    def test_create_translation_memory(self):
        response = self.api_client.post(
            "/api/translation-memories/",
            {
                "name": "Test TM",
                "source_language": "en",
                "target_language": "fr",
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["name"], "Test TM")

    def test_create_sets_created_by(self):
        self.api_client.post(
            "/api/translation-memories/",
            {
                "name": "TM Created By",
                "source_language": "en",
                "target_language": "fr",
            },
        )
        tm = TranslationMemory.objects.get(name="TM Created By")
        self.assertEqual(tm.created_by, self.admin_user)

    def test_retrieve_translation_memory(self):
        tm = TranslationMemory.objects.create(
            name="Test TM",
            source_language=self.source_lang,
            target_language=self.target_lang,
            created_by=self.admin_user,
        )
        response = self.api_client.get(f"/api/translation-memories/{tm.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("uuid", response.data)

    def test_update_translation_memory(self):
        tm = TranslationMemory.objects.create(
            name="Old TM",
            source_language=self.source_lang,
            target_language=self.target_lang,
            created_by=self.admin_user,
        )
        response = self.api_client.patch(
            f"/api/translation-memories/{tm.id}/",
            {"name": "New TM"},
        )
        self.assertEqual(response.status_code, 200)
        tm.refresh_from_db()
        self.assertEqual(tm.name, "New TM")

    def test_delete_translation_memory(self):
        tm = TranslationMemory.objects.create(
            name="To Delete",
            source_language=self.source_lang,
            target_language=self.target_lang,
            created_by=self.admin_user,
        )
        response = self.api_client.delete(f"/api/translation-memories/{tm.id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(TranslationMemory.objects.filter(id=tm.id).exists())

    def test_filter_by_client_name(self):
        TranslationMemory.objects.create(
            name="TM1",
            source_language=self.source_lang,
            target_language=self.target_lang,
            created_by=self.admin_user,
            client=self.client_obj,
        )
        TranslationMemory.objects.create(
            name="TM2",
            source_language=self.source_lang,
            target_language=self.target_lang,
            created_by=self.admin_user,
        )
        response = self.api_client.get("/api/translation-memories/?client_name=Acme")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], "TM1")

    def test_filter_by_source_language(self):
        TranslationMemory.objects.create(
            name="TM1",
            source_language=self.source_lang,
            target_language=self.target_lang,
            created_by=self.admin_user,
        )
        response = self.api_client.get("/api/translation-memories/?source_language=en")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data["results"]), 1)

    def test_filter_by_target_language(self):
        TranslationMemory.objects.create(
            name="TM1",
            source_language=self.source_lang,
            target_language=self.target_lang,
            created_by=self.admin_user,
        )
        response = self.api_client.get("/api/translation-memories/?target_language=fr")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data["results"]), 1)


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------


class UserViewSetTests(APITestBase):
    def test_list_users(self):
        response = self.api_client.get("/api/users/")
        self.assertEqual(response.status_code, 200)

    def test_create_user(self):
        response = self.api_client.post(
            "/api/users/",
            {"username": "newuser", "password": "SecurePass1!", "is_active": True},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_create_user_password_hashed(self):
        self.api_client.post(
            "/api/users/",
            {"username": "hashtest", "password": "SecurePass1!", "is_active": True},
            format="json",
        )
        user = User.objects.get(username="hashtest")
        self.assertTrue(user.check_password("SecurePass1!"))
        self.assertNotEqual(user.password, "SecurePass1!")

    def test_create_user_password_not_in_response(self):
        response = self.api_client.post(
            "/api/users/",
            {"username": "nopwdresp", "password": "SecurePass1!", "is_active": True},
            format="json",
        )
        self.assertNotIn("password", response.data)

    def test_retrieve_user(self):
        response = self.api_client.get(f"/api/users/{self.admin_user.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("password", response.data)
        self.assertEqual(response.data["username"], "admin")

    def test_update_user(self):
        response = self.api_client.patch(
            f"/api/users/{self.admin_user.id}/",
            {"email": "admin@example.com"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.admin_user.refresh_from_db()
        self.assertEqual(self.admin_user.email, "admin@example.com")

    def test_delete_user(self):
        user = User.objects.create_user("todelete", password="Testpass123!")
        response = self.api_client.delete(f"/api/users/{user.id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(User.objects.filter(id=user.id).exists())

    def test_filter_by_username(self):
        response = self.api_client.get("/api/users/?username=admin")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["username"], "admin")

    def test_serializer_fields(self):
        response = self.api_client.get(f"/api/users/{self.admin_user.id}/")
        expected_fields = {"id", "username", "email", "is_active", "groups"}
        self.assertEqual(set(response.data.keys()), expected_fields)


# ---------------------------------------------------------------------------
# Authentication & Permissions
# ---------------------------------------------------------------------------


class AuthenticationPermissionTests(TestCase):
    @mock.patch("kaplancloudapp.models.Path.mkdir", mock.MagicMock())
    def setUp(self):
        self.admin_user = User.objects.create_user(
            "admin", password="Testpass123!", is_staff=True
        )
        self.regular_user = User.objects.create_user(
            "regular", password="Testpass123!", is_staff=False
        )

    def test_unauthenticated_list_returns_401_or_403(self):
        client = APIClient()
        response = client.get("/api/clients/")
        self.assertIn(response.status_code, [401, 403])

    def test_unauthenticated_create_returns_401_or_403(self):
        client = APIClient()
        response = client.post("/api/clients/", {"name": "Test"})
        self.assertIn(response.status_code, [401, 403])

    def test_non_staff_user_returns_403(self):
        client = APIClient()
        client.force_authenticate(user=self.regular_user)
        response = client.get("/api/clients/")
        self.assertEqual(response.status_code, 403)

    def test_staff_user_returns_200(self):
        client = APIClient()
        client.force_authenticate(user=self.admin_user)
        response = client.get("/api/clients/")
        self.assertEqual(response.status_code, 200)

    def test_token_auth_works(self):
        token = Token.objects.create(user=self.admin_user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        response = client.get("/api/clients/")
        self.assertEqual(response.status_code, 200)

    def test_basic_auth_works(self):
        import base64

        client = APIClient()
        credentials = base64.b64encode(b"admin:Testpass123!").decode()
        client.credentials(HTTP_AUTHORIZATION=f"Basic {credentials}")
        response = client.get("/api/clients/")
        self.assertEqual(response.status_code, 200)

    def test_permission_enforced_on_all_endpoints(self):
        client = APIClient()
        endpoints = [
            "/api/clients/",
            "/api/groups/",
            "/api/language-profiles/",
            "/api/projects/",
            "/api/project-webhooks/",
            "/api/project-files/",
            "/api/project-file-webhooks/",
            "/api/project-reference-files/",
            "/api/translation-memories/",
            "/api/users/",
        ]
        for endpoint in endpoints:
            response = client.get(endpoint)
            self.assertIn(
                response.status_code,
                [401, 403],
                f"{endpoint} should reject unauthenticated requests",
            )


# ---------------------------------------------------------------------------
# WebHook Models
# ---------------------------------------------------------------------------


class WebHookModelTests(TestCase):
    @mock.patch("kaplancloudapp.models.Path.mkdir", mock.MagicMock())
    def setUp(self):
        self.user = User.objects.create_user(
            "admin", password="Testpass123!", is_staff=True
        )
        self.source_lang = LanguageProfile.objects.create(
            name="English", iso_code="en", created_by=self.user
        )
        self.target_lang = LanguageProfile.objects.create(
            name="French", iso_code="fr", created_by=self.user
        )
        self.project = Project.objects.create(
            name="Test",
            source_language=self.source_lang,
            target_language=self.target_lang,
            created_by=self.user,
            directory="test",
        )

    @mock.patch("kaplancloudapi.models.requests.post")
    def test_project_webhook_fire_hook(self, mock_post):
        webhook = ProjectWebHook.objects.create(
            target="https://example.com/hook",
            header={"X-Custom": "value"},
            project=self.project,
        )
        webhook.fire_hook()
        mock_post.assert_called_once_with(
            "https://example.com/hook",
            data=mock.ANY,
            headers={"X-Custom": "value"},
        )

    @mock.patch("kaplancloudapp.models.NewFileThread")
    @mock.patch("kaplancloudapi.models.requests.post")
    def test_project_file_webhook_fire_hook(self, mock_post, mock_thread):
        pf = ProjectFile.objects.create(name="test.xlf", project=self.project, status=0)
        webhook = ProjectFileWebHook.objects.create(
            target="https://example.com/file-hook",
            header={},
            project_file=pf,
        )
        webhook.fire_hook()
        mock_post.assert_called_once_with(
            "https://example.com/file-hook",
            data=mock.ANY,
            headers={},
        )

    @mock.patch(
        "kaplancloudapi.models.requests.post",
        side_effect=Exception("connection error"),
    )
    def test_fire_hook_handles_exception(self, mock_post):
        webhook = ProjectWebHook.objects.create(
            target="https://example.com/hook",
            header={},
            project=self.project,
        )
        # Should not raise
        webhook.fire_hook()


# ---------------------------------------------------------------------------
# WebHook Signals
# ---------------------------------------------------------------------------


class WebHookSignalTests(TestCase):
    @mock.patch("kaplancloudapp.models.Path.mkdir", mock.MagicMock())
    def setUp(self):
        self.user = User.objects.create_user(
            "admin", password="Testpass123!", is_staff=True
        )
        self.source_lang = LanguageProfile.objects.create(
            name="English", iso_code="en", created_by=self.user
        )
        self.target_lang = LanguageProfile.objects.create(
            name="French", iso_code="fr", created_by=self.user
        )

    @mock.patch("kaplancloudapi.models.requests.post")
    def test_project_save_fires_webhooks(self, mock_post):
        project = Project.objects.create(
            name="Test",
            source_language=self.source_lang,
            target_language=self.target_lang,
            created_by=self.user,
            directory="test",
        )
        ProjectWebHook.objects.create(
            target="https://example.com/hook",
            header={},
            project=project,
        )
        mock_post.reset_mock()
        project.status = 3
        project.save()
        mock_post.assert_called()

    @mock.patch("kaplancloudapi.models.requests.post")
    def test_project_save_fires_multiple_webhooks(self, mock_post):
        project = Project.objects.create(
            name="Test",
            source_language=self.source_lang,
            target_language=self.target_lang,
            created_by=self.user,
            directory="test",
        )
        ProjectWebHook.objects.create(
            target="https://example.com/hook1",
            header={},
            project=project,
        )
        ProjectWebHook.objects.create(
            target="https://example.com/hook2",
            header={},
            project=project,
        )
        mock_post.reset_mock()
        project.status = 3
        project.save()
        self.assertEqual(mock_post.call_count, 2)

    @mock.patch("kaplancloudapp.models.NewFileThread")
    @mock.patch("kaplancloudapi.models.requests.post")
    def test_project_file_save_fires_webhooks(self, mock_post, mock_thread):
        project = Project.objects.create(
            name="Test",
            source_language=self.source_lang,
            target_language=self.target_lang,
            created_by=self.user,
            directory="test",
        )
        pf = ProjectFile.objects.create(name="test.xlf", project=project, status=0)
        ProjectFileWebHook.objects.create(
            target="https://example.com/file-hook",
            header={},
            project_file=pf,
        )
        mock_post.reset_mock()
        pf.name = "renamed.xlf"
        pf.save()
        mock_post.assert_called()

    @mock.patch("kaplancloudapi.models.requests.post")
    def test_unrelated_webhook_not_fired(self, mock_post):
        project_a = Project.objects.create(
            name="A",
            source_language=self.source_lang,
            target_language=self.target_lang,
            created_by=self.user,
            directory="test-a",
        )
        project_b = Project.objects.create(
            name="B",
            source_language=self.source_lang,
            target_language=self.target_lang,
            created_by=self.user,
            directory="test-b",
        )
        ProjectWebHook.objects.create(
            target="https://example.com/hook-a",
            header={},
            project=project_a,
        )
        mock_post.reset_mock()
        project_b.status = 3
        project_b.save()
        mock_post.assert_not_called()
