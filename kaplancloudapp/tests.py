from unittest.mock import MagicMock, patch

from django.contrib.auth.models import Permission, User
from django.test import TestCase
from lxml import etree

from .forms import (
    AssignLinguistForm,
    SearchForm,
    SegmentCommentForm,
    TranslationMemoryForm,
    TranslationMemoryImportForm,
)
from .models import (
    Client,
    Comment,
    LanguageProfile,
    Project,
    ProjectFile,
    ProjectReport,
    Segment,
    SegmentUpdate,
    TBEntry,
    Termbase,
    TMEntry,
    TMEntryUpdate,
    TranslationMemory,
)
from .utils import trim_segment

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_languages():
    """Create English and French language profiles."""
    en = LanguageProfile.objects.create(name="English", iso_code="en", is_ltr=True)
    fr = LanguageProfile.objects.create(name="French", iso_code="fr", is_ltr=True)
    return en, fr


def _make_project(user, en, fr, **kwargs):
    """Create a project with directory pre-set to avoid save-loop."""
    defaults = {
        "name": "Test Project",
        "source_language": en,
        "target_language": fr,
        "created_by": user,
        "directory": "/tmp/test-project",
    }
    defaults.update(kwargs)
    return Project.objects.create(**defaults)


def _pm_user(username="pm"):
    """Create a user with all kaplancloudapp permissions."""
    user = User.objects.create_user(username, password="Testpass123!")
    for perm in Permission.objects.filter(content_type__app_label="kaplancloudapp"):
        user.user_permissions.add(perm)
    return user


# ===========================================================================
# Utility tests
# ===========================================================================


class TrimSegmentTests(TestCase):
    def test_extracts_inner_text(self):
        elem = etree.fromstring("<source>Hello world</source>")
        self.assertEqual(trim_segment(elem), "Hello world")

    def test_self_closing_tag_returns_empty(self):
        elem = etree.fromstring("<source/>")
        self.assertEqual(trim_segment(elem), "")

    def test_preserves_inner_tags(self):
        elem = etree.fromstring("<target>Hello <b>world</b></target>")
        result = trim_segment(elem)
        self.assertIn("world", result)


# ===========================================================================
# Model tests
# ===========================================================================


class LanguageProfileModelTests(TestCase):
    def test_str(self):
        lp = LanguageProfile.objects.create(name="English", iso_code="en", is_ltr=True)
        self.assertEqual(str(lp), "English")

    def test_ordering(self):
        LanguageProfile.objects.create(name="French", iso_code="fr")
        LanguageProfile.objects.create(name="Arabic", iso_code="ar", is_ltr=False)
        LanguageProfile.objects.create(name="English", iso_code="en")
        names = list(LanguageProfile.objects.values_list("name", flat=True))
        self.assertEqual(names, ["Arabic", "English", "French"])

    def test_primary_key_is_iso_code(self):
        lp = LanguageProfile.objects.create(name="German", iso_code="de")
        self.assertEqual(lp.pk, "de")

    def test_default_is_ltr(self):
        lp = LanguageProfile.objects.create(name="Spanish", iso_code="es")
        self.assertTrue(lp.is_ltr)

    def test_user_set_null_on_delete(self):
        user = User.objects.create_user("u1", password="Testpass123!")
        lp = LanguageProfile.objects.create(
            name="Italian", iso_code="it", created_by=user
        )
        user.delete()
        lp.refresh_from_db()
        self.assertIsNone(lp.created_by)


class ClientModelTests(TestCase):
    def test_str(self):
        client = Client.objects.create(name="Acme")
        self.assertEqual(str(client), f"{client.id}-Acme")

    def test_team_many_to_many(self):
        client = Client.objects.create(name="Acme")
        u1 = User.objects.create_user("u1", password="p")
        u2 = User.objects.create_user("u2", password="p")
        client.team.add(u1, u2)
        self.assertEqual(client.team.count(), 2)


class TermbaseModelTests(TestCase):
    def setUp(self):
        self.en, self.fr = _make_languages()

    def test_creation(self):
        tb = Termbase.objects.create(
            name="Test TB", source_language=self.en, target_language=self.fr
        )
        self.assertIsNotNone(tb.uuid)
        self.assertIsNotNone(tb.created_at)

    def test_uuid_is_unique(self):
        tb1 = Termbase.objects.create(
            name="TB1", source_language=self.en, target_language=self.fr
        )
        tb2 = Termbase.objects.create(
            name="TB2", source_language=self.en, target_language=self.fr
        )
        self.assertNotEqual(tb1.uuid, tb2.uuid)


class TBEntryModelTests(TestCase):
    def setUp(self):
        en, fr = _make_languages()
        self.tb = Termbase.objects.create(
            name="TB", source_language=en, target_language=fr
        )

    def test_creation(self):
        entry = TBEntry.objects.create(
            source="hello", target="bonjour", termbase=self.tb
        )
        self.assertEqual(entry.source, "hello")

    def test_cascade_delete(self):
        TBEntry.objects.create(source="a", target="b", termbase=self.tb)
        self.tb.delete()
        self.assertEqual(TBEntry.objects.count(), 0)


class TranslationMemoryModelTests(TestCase):
    def setUp(self):
        self.en, self.fr = _make_languages()

    def test_verbose_name_plural(self):
        self.assertEqual(
            TranslationMemory._meta.verbose_name_plural, "Translation memories"
        )

    def test_get_absolute_url(self):
        tm = TranslationMemory.objects.create(
            name="TM1", source_language=self.en, target_language=self.fr
        )
        self.assertEqual(tm.get_absolute_url(), f"/translation-memory/{tm.uuid}")

    def test_uuid_auto_generated(self):
        tm = TranslationMemory.objects.create(
            name="TM", source_language=self.en, target_language=self.fr
        )
        self.assertIsNotNone(tm.uuid)


class TMEntryModelTests(TestCase):
    def setUp(self):
        en, fr = _make_languages()
        self.tm = TranslationMemory.objects.create(
            name="TM", source_language=en, target_language=fr
        )

    def test_save_creates_update_when_target_nonempty(self):
        user = User.objects.create_user("u1", password="p")
        entry = TMEntry(
            source="hello",
            target="bonjour",
            translationmemory=self.tm,
            created_by=user,
        )
        entry.save()
        self.assertEqual(TMEntryUpdate.objects.filter(tmentry=entry).count(), 1)
        update = TMEntryUpdate.objects.get(tmentry=entry)
        self.assertEqual(update.source, "hello")
        self.assertEqual(update.target, "bonjour")
        self.assertEqual(update.submitted_by, user)

    def test_save_no_update_when_target_empty(self):
        entry = TMEntry(source="hello", target="", translationmemory=self.tm)
        entry.save()
        self.assertEqual(TMEntryUpdate.objects.filter(tmentry=entry).count(), 0)

    def test_save_uses_updated_by_over_created_by(self):
        u1 = User.objects.create_user("creator", password="p")
        u2 = User.objects.create_user("updater", password="p")
        entry = TMEntry(
            source="a",
            target="b",
            translationmemory=self.tm,
            created_by=u1,
            updated_by=u2,
        )
        entry.save()
        update = TMEntryUpdate.objects.get(tmentry=entry)
        self.assertEqual(update.submitted_by, u2)

    def test_cascade_delete(self):
        entry = TMEntry.objects.create(source="a", target="", translationmemory=self.tm)
        self.tm.delete()
        self.assertFalse(TMEntry.objects.filter(pk=entry.pk).exists())


class ProjectModelTests(TestCase):
    def setUp(self):
        self.en, self.fr = _make_languages()
        self.user = User.objects.create_user("pm", password="Testpass123!")

    def test_str(self):
        project = _make_project(self.user, self.en, self.fr, name="MyProj")
        self.assertEqual(str(project), f"{project.id}-MyProj")

    def test_ordering_newest_first(self):
        p1 = _make_project(self.user, self.en, self.fr, name="First")
        p2 = _make_project(self.user, self.en, self.fr, name="Second")
        ids = list(Project.objects.values_list("id", flat=True))
        self.assertEqual(ids, [p2.id, p1.id])

    def test_get_absolute_url(self):
        project = _make_project(self.user, self.en, self.fr)
        self.assertEqual(project.get_absolute_url(), f"/project/{project.uuid}")

    def test_get_status(self):
        project = _make_project(self.user, self.en, self.fr, status=0)
        self.assertEqual(project.get_status(), "Preparing")
        project.status = 6
        self.assertEqual(project.get_status(), "Complete")

    def test_save_sets_directory_when_blank(self):
        project = Project(
            name="AutoDir",
            source_language=self.en,
            target_language=self.fr,
            created_by=self.user,
            directory="",
        )
        project.save()
        self.assertIn(str(project.uuid), project.directory)

    def test_default_status_is_preparing(self):
        project = _make_project(self.user, self.en, self.fr)
        self.assertEqual(project.status, 0)


class ProjectFileModelTests(TestCase):
    def setUp(self):
        en, fr = _make_languages()
        self.user = User.objects.create_user("pm", password="Testpass123!")
        self.project = _make_project(self.user, en, fr)

    @patch("kaplancloudapp.models.NewFileThread")
    def test_str(self, mock_thread):
        mock_thread.return_value.run = MagicMock()
        pf = ProjectFile.objects.create(name="test.xliff", project=self.project)
        self.assertIn("test.xliff", str(pf))
        self.assertIn(str(self.project.id), str(pf))

    @patch("kaplancloudapp.models.NewFileThread")
    def test_get_absolute_url(self, mock_thread):
        mock_thread.return_value.run = MagicMock()
        pf = ProjectFile.objects.create(name="test.xliff", project=self.project)
        self.assertEqual(pf.get_absolute_url(), f"/file/{pf.uuid}")

    @patch("kaplancloudapp.models.NewFileThread")
    def test_get_status(self, mock_thread):
        mock_thread.return_value.run = MagicMock()
        pf = ProjectFile.objects.create(
            name="test.xliff", project=self.project, status=3
        )
        self.assertEqual(pf.get_status(), "Ready for Translation")

    @patch("kaplancloudapp.models.NewFileThread")
    def test_get_source_directory(self, mock_thread):
        mock_thread.return_value.run = MagicMock()
        pf = ProjectFile.objects.create(name="test.xliff", project=self.project)
        src_dir = pf.get_source_directory()
        self.assertIn(self.project.source_language.iso_code, str(src_dir))

    @patch("kaplancloudapp.models.NewFileThread")
    def test_get_target_directory(self, mock_thread):
        mock_thread.return_value.run = MagicMock()
        pf = ProjectFile.objects.create(name="test.xliff", project=self.project)
        tgt_dir = pf.get_target_directory()
        self.assertIn(self.project.target_language.iso_code, str(tgt_dir))

    @patch("kaplancloudapp.models.NewFileThread")
    def test_ordering_by_name(self, mock_thread):
        mock_thread.return_value.run = MagicMock()
        ProjectFile.objects.create(name="b.xliff", project=self.project)
        # Need a different project to avoid unique_together constraint
        en2 = LanguageProfile.objects.get(iso_code="en")
        fr2 = LanguageProfile.objects.get(iso_code="fr")
        p2 = _make_project(self.user, en2, fr2, name="P2")
        ProjectFile.objects.create(name="a.xliff", project=p2)
        names = list(ProjectFile.objects.values_list("name", flat=True))
        self.assertEqual(names, ["a.xliff", "b.xliff"])

    @patch("kaplancloudapp.models.NewFileThread")
    def test_unique_together_name_project(self, mock_thread):
        mock_thread.return_value.run = MagicMock()
        ProjectFile.objects.create(name="dup.xliff", project=self.project)
        with self.assertRaises(Exception):
            ProjectFile.objects.create(name="dup.xliff", project=self.project)

    @patch("kaplancloudapp.models.NewFileThread")
    def test_new_file_triggers_thread(self, mock_thread):
        mock_thread.return_value.run = MagicMock()
        ProjectFile.objects.create(name="trigger.xliff", project=self.project)
        mock_thread.assert_called_once()
        mock_thread.return_value.run.assert_called_once()

    @patch("kaplancloudapp.models.NewFileThread")
    def test_status_3_with_translator_advances_to_4(self, mock_thread):
        mock_thread.return_value.run = MagicMock()
        translator = User.objects.create_user("translator", password="p")
        pf = ProjectFile.objects.create(name="adv.xliff", project=self.project)
        pf.status = 3
        pf.translator = translator
        pf.save()
        pf.refresh_from_db()
        self.assertEqual(pf.status, 4)


class SegmentModelTests(TestCase):
    def setUp(self):
        en, fr = _make_languages()
        user = User.objects.create_user("pm", password="p")
        self.project = _make_project(user, en, fr)

    @patch("kaplancloudapp.models.NewFileThread")
    def test_get_status(self, mock_thread):
        mock_thread.return_value.run = MagicMock()
        pf = ProjectFile.objects.create(name="f.xliff", project=self.project)
        seg = Segment.objects.create(tu_id=1, s_id=1, source="hello", file=pf)
        self.assertEqual(seg.get_status(), "Blank")
        seg.status = 2
        self.assertEqual(seg.get_status(), "Translated")

    @patch("kaplancloudapp.models.NewFileThread")
    def test_save_with_no_override_skips_processing(self, mock_thread):
        mock_thread.return_value.run = MagicMock()
        pf = ProjectFile.objects.create(name="f.xliff", project=self.project)
        seg = Segment.objects.create(tu_id=1, s_id=1, source="hello", file=pf)
        seg.target = "bonjour"
        seg.save(no_override=True)
        self.assertEqual(SegmentUpdate.objects.count(), 0)


class CommentModelTests(TestCase):
    @patch("kaplancloudapp.models.NewFileThread")
    def test_creation(self, mock_thread):
        mock_thread.return_value.run = MagicMock()
        en, fr = _make_languages()
        user = User.objects.create_user("pm", password="p")
        project = _make_project(user, en, fr)
        pf = ProjectFile.objects.create(name="f.xliff", project=project)
        seg = Segment.objects.create(tu_id=1, s_id=1, source="hello", file=pf)
        comment = Comment.objects.create(comment="Nice!", segment=seg, created_by=user)
        self.assertEqual(comment.comment, "Nice!")
        self.assertTrue(comment.is_active)
        self.assertIsNotNone(comment.created_at)

    @patch("kaplancloudapp.models.NewFileThread")
    def test_cascade_on_segment_delete(self, mock_thread):
        mock_thread.return_value.run = MagicMock()
        en, fr = _make_languages()
        user = User.objects.create_user("pm", password="p")
        project = _make_project(user, en, fr)
        pf = ProjectFile.objects.create(name="f.xliff", project=project)
        seg = Segment.objects.create(tu_id=1, s_id=1, source="hi", file=pf)
        Comment.objects.create(comment="c", segment=seg)
        seg.delete()
        self.assertEqual(Comment.objects.count(), 0)


class ProjectReportModelTests(TestCase):
    def setUp(self):
        en, fr = _make_languages()
        self.user = User.objects.create_user("pm", password="p")
        self.project = _make_project(self.user, en, fr)

    def test_get_absolute_url(self):
        report = ProjectReport.objects.create(
            project=self.project, content={"test": True}
        )
        self.assertEqual(report.get_absolute_url(), f"/report/{report.uuid}")

    def test_ordering_newest_first(self):
        r1 = ProjectReport.objects.create(project=self.project, content={"n": 1})
        r2 = ProjectReport.objects.create(project=self.project, content={"n": 2})
        ids = list(ProjectReport.objects.values_list("id", flat=True))
        self.assertEqual(ids, [r2.id, r1.id])

    @patch("kaplancloudapp.models.NewProjectReportThread")
    def test_save_with_status_1_triggers_thread(self, mock_thread):
        mock_thread.return_value.run = MagicMock()
        report = ProjectReport.objects.create(
            project=self.project, content={"s": "processing"}
        )
        report.status = 1
        report.save()
        mock_thread.assert_called_once()
        mock_thread.return_value.run.assert_called_once()


# ===========================================================================
# Form tests
# ===========================================================================


class AssignLinguistFormTests(TestCase):
    def test_valid_form(self):
        User.objects.create_user("translator1", password="p")
        form = AssignLinguistForm(
            data={
                "username": "translator1",
                "role": "0",
                "file_uuids": "abc-123",
            }
        )
        self.assertTrue(form.is_valid())

    def test_invalid_username(self):
        form = AssignLinguistForm(
            data={
                "username": "nonexistent",
                "role": "0",
                "file_uuids": "abc-123",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)

    def test_override_not_required(self):
        User.objects.create_user("t", password="p")
        form = AssignLinguistForm(
            data={"username": "t", "role": "0", "file_uuids": "x"}
        )
        self.assertTrue(form.is_valid())
        self.assertFalse(form.cleaned_data["override"])


class SearchFormTests(TestCase):
    def test_empty_form_is_valid(self):
        form = SearchForm(data={})
        self.assertTrue(form.is_valid())

    def test_with_language_filter(self):
        en = LanguageProfile.objects.create(name="English", iso_code="en")
        form = SearchForm(data={"source": en.iso_code})
        self.assertTrue(form.is_valid())


class SegmentCommentFormTests(TestCase):
    def test_valid(self):
        form = SegmentCommentForm(data={"comment": "A comment"})
        self.assertTrue(form.is_valid())

    def test_empty_comment_invalid(self):
        form = SegmentCommentForm(data={"comment": ""})
        self.assertFalse(form.is_valid())


class TranslationMemoryFormTests(TestCase):
    def setUp(self):
        self.en, self.fr = _make_languages()

    def test_valid_form(self):
        form = TranslationMemoryForm(
            data={
                "name": "My TM",
                "source_language": self.en.iso_code,
                "target_language": self.fr.iso_code,
            }
        )
        self.assertTrue(form.is_valid())

    def test_missing_name_invalid(self):
        form = TranslationMemoryForm(
            data={
                "name": "",
                "source_language": self.en.iso_code,
                "target_language": self.fr.iso_code,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)


class TranslationMemoryImportFormTests(TestCase):
    def test_invalid_extension(self):
        mock_file = MagicMock()
        mock_file.name = "data.csv"
        mock_file.size = 100
        form = TranslationMemoryImportForm(
            data={"source_language": "en", "target_language": "fr"},
            files={"tm_file": mock_file},
        )
        self.assertFalse(form.is_valid())
        self.assertIn("tm_file", form.errors)


# ===========================================================================
# View tests
# ===========================================================================


class ProjectsViewTests(TestCase):
    def setUp(self):
        self.en, self.fr = _make_languages()
        self.user = _pm_user()

    def test_login_required(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_authenticated_get(self):
        self.client.login(username="pm", password="Testpass123!")
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "projects.html")

    def test_filter_by_source_language(self):
        self.client.login(username="pm", password="Testpass123!")
        _make_project(self.user, self.en, self.fr, name="EN-FR")
        response = self.client.get("/", {"source": "en"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["display_form"])

    def test_filter_by_client(self):
        self.client.login(username="pm", password="Testpass123!")
        client = Client.objects.create(name="TestClient")
        _make_project(self.user, self.en, self.fr, client=client)
        response = self.client.get("/", {"client": client.id})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["display_form"])

    def test_non_pm_sees_only_own_projects(self):
        regular = User.objects.create_user("regular", password="Testpass123!")
        other = User.objects.create_user("other", password="Testpass123!")
        _make_project(self.user, self.en, self.fr, name="PM Project")
        _make_project(regular, self.en, self.fr, name="Regular Project")
        _make_project(other, self.en, self.fr, name="Other Project")
        self.client.login(username="regular", password="Testpass123!")
        response = self.client.get("/")
        project_names = [p.name for p in response.context["projects"]]
        self.assertIn("Regular Project", project_names)
        self.assertNotIn("Other Project", project_names)


class ProjectDetailViewTests(TestCase):
    def setUp(self):
        self.en, self.fr = _make_languages()
        self.user = _pm_user()
        self.project = _make_project(self.user, self.en, self.fr)

    def test_login_required(self):
        response = self.client.get(f"/project/{self.project.uuid}")
        self.assertEqual(response.status_code, 302)

    def test_creator_can_view(self):
        self.client.login(username="pm", password="Testpass123!")
        response = self.client.get(f"/project/{self.project.uuid}")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "project.html")

    def test_context_contains_project(self):
        self.client.login(username="pm", password="Testpass123!")
        response = self.client.get(f"/project/{self.project.uuid}")
        self.assertEqual(response.context["project"], self.project)

    def test_unrelated_user_redirected(self):
        User.objects.create_user("outsider", password="Testpass123!")
        self.client.login(username="outsider", password="Testpass123!")
        response = self.client.get(f"/project/{self.project.uuid}")
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_forbidden_for_non_pm_post(self):
        self.client.login(username="pm", password="Testpass123!")
        # Remove change_project perm
        perm = Permission.objects.get(
            codename="change_project",
            content_type__app_label="kaplancloudapp",
        )
        self.user.user_permissions.remove(perm)
        # Clear perm cache
        self.user = User.objects.get(pk=self.user.pk)
        response = self.client.post(
            f"/project/{self.project.uuid}",
            {"task": "analyze", "file_uuids": "fake-uuid"},
        )
        self.assertEqual(response.status_code, 403)


class NewProjectViewTests(TestCase):
    def setUp(self):
        _make_languages()
        self.user = _pm_user()

    def test_login_required(self):
        response = self.client.get("/project/new")
        self.assertEqual(response.status_code, 302)

    def test_permission_required(self):
        User.objects.create_user("noperm", password="Testpass123!")
        self.client.login(username="noperm", password="Testpass123!")
        response = self.client.get("/project/new")
        self.assertEqual(response.status_code, 302)

    def test_pm_can_access_form(self):
        self.client.login(username="pm", password="Testpass123!")
        response = self.client.get("/project/new")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "newproject.html")


class NewTMViewTests(TestCase):
    def setUp(self):
        self.en, self.fr = _make_languages()
        self.user = _pm_user()

    def test_login_required(self):
        response = self.client.get("/translation-memory/new")
        self.assertEqual(response.status_code, 302)

    def test_permission_required(self):
        User.objects.create_user("noperm", password="Testpass123!")
        self.client.login(username="noperm", password="Testpass123!")
        response = self.client.get("/translation-memory/new")
        self.assertEqual(response.status_code, 302)

    def test_pm_can_access_form(self):
        self.client.login(username="pm", password="Testpass123!")
        response = self.client.get("/translation-memory/new")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "newtm.html")

    def test_valid_post_creates_tm(self):
        self.client.login(username="pm", password="Testpass123!")
        response = self.client.post(
            "/translation-memory/new",
            {
                "name": "New TM",
                "source_language": self.en.iso_code,
                "target_language": self.fr.iso_code,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(TranslationMemory.objects.filter(name="New TM").exists())

    def test_created_tm_has_user(self):
        self.client.login(username="pm", password="Testpass123!")
        self.client.post(
            "/translation-memory/new",
            {
                "name": "TM With User",
                "source_language": self.en.iso_code,
                "target_language": self.fr.iso_code,
            },
        )
        tm = TranslationMemory.objects.get(name="TM With User")
        self.assertEqual(tm.created_by, self.user)


class TranslationMemoriesViewTests(TestCase):
    def setUp(self):
        self.en, self.fr = _make_languages()
        self.user = _pm_user()

    def test_login_required(self):
        response = self.client.get("/translation-memories")
        self.assertEqual(response.status_code, 302)

    def test_authenticated_get(self):
        self.client.login(username="pm", password="Testpass123!")
        response = self.client.get("/translation-memories")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "translation-memories.html")

    def test_json_format(self):
        self.client.login(username="pm", password="Testpass123!")
        tm = TranslationMemory.objects.create(
            name="JSONTEST", source_language=self.en, target_language=self.fr
        )
        response = self.client.get("/translation-memories", {"format": "JSON"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn(str(tm.id), data)
        self.assertEqual(data[str(tm.id)], "JSONTEST")

    def test_filter_by_source_language(self):
        self.client.login(username="pm", password="Testpass123!")
        TranslationMemory.objects.create(
            name="TM1", source_language=self.en, target_language=self.fr
        )
        response = self.client.get("/translation-memories", {"source": "en"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["display_form"])

    def test_non_pm_sees_only_client_tms(self):
        regular = User.objects.create_user("regular", password="Testpass123!")
        client = Client.objects.create(name="Client1")
        client.team.add(regular)
        TranslationMemory.objects.create(
            name="ClientTM",
            source_language=self.en,
            target_language=self.fr,
            client=client,
        )
        TranslationMemory.objects.create(
            name="NoClientTM", source_language=self.en, target_language=self.fr
        )
        self.client.login(username="regular", password="Testpass123!")
        response = self.client.get("/translation-memories")
        tm_names = [tm.name for tm in response.context["tms"]]
        self.assertIn("ClientTM", tm_names)
        self.assertNotIn("NoClientTM", tm_names)


class TranslationMemoryDetailViewTests(TestCase):
    def setUp(self):
        en, fr = _make_languages()
        self.user = _pm_user()
        self.tm = TranslationMemory.objects.create(
            name="TM", source_language=en, target_language=fr
        )

    def test_login_required(self):
        response = self.client.get(f"/translation-memory/{self.tm.uuid}")
        self.assertEqual(response.status_code, 302)

    def test_pm_can_view(self):
        self.client.login(username="pm", password="Testpass123!")
        response = self.client.get(f"/translation-memory/{self.tm.uuid}")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tm.html")

    def test_excludes_empty_target_entries(self):
        self.client.login(username="pm", password="Testpass123!")
        TMEntry.objects.create(source="a", target="", translationmemory=self.tm)
        TMEntry.objects.create(
            source="b", target="translated", translationmemory=self.tm
        )
        response = self.client.get(f"/translation-memory/{self.tm.uuid}")
        self.assertEqual(response.context["tm_entries"].count(), 1)


class TMImportViewTests(TestCase):
    def setUp(self):
        en, fr = _make_languages()
        self.user = _pm_user()
        self.tm = TranslationMemory.objects.create(
            name="TM", source_language=en, target_language=fr
        )

    def test_login_required(self):
        response = self.client.get(f"/translation-memory/{self.tm.uuid}/import")
        self.assertEqual(response.status_code, 302)

    def test_pm_can_access_form(self):
        self.client.login(username="pm", password="Testpass123!")
        response = self.client.get(f"/translation-memory/{self.tm.uuid}/import")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tm-import.html")


class EditorViewTests(TestCase):
    def setUp(self):
        en, fr = _make_languages()
        self.user = _pm_user()
        self.project = _make_project(self.user, en, fr)

    @patch("kaplancloudapp.models.NewFileThread")
    def test_login_required(self, mock_thread):
        mock_thread.return_value.run = MagicMock()
        pf = ProjectFile.objects.create(name="e.xliff", project=self.project)
        response = self.client.get(f"/file/{pf.uuid}")
        self.assertEqual(response.status_code, 302)

    @patch("kaplancloudapp.models.NewFileThread")
    def test_creator_can_view(self, mock_thread):
        mock_thread.return_value.run = MagicMock()
        pf = ProjectFile.objects.create(name="e.xliff", project=self.project, status=4)
        self.client.login(username="pm", password="Testpass123!")
        response = self.client.get(f"/file/{pf.uuid}")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "editor.html")

    @patch("kaplancloudapp.models.NewFileThread")
    def test_unrelated_user_redirected(self, mock_thread):
        mock_thread.return_value.run = MagicMock()
        User.objects.create_user("outsider", password="Testpass123!")
        pf = ProjectFile.objects.create(name="e.xliff", project=self.project, status=4)
        self.client.login(username="outsider", password="Testpass123!")
        response = self.client.get(f"/file/{pf.uuid}")
        self.assertEqual(response.status_code, 302)

    @patch("kaplancloudapp.models.NewFileThread")
    def test_translator_can_view_in_translation(self, mock_thread):
        mock_thread.return_value.run = MagicMock()
        translator = User.objects.create_user("translator", password="Testpass123!")
        pf = ProjectFile.objects.create(
            name="e.xliff",
            project=self.project,
            status=4,
            translator=translator,
        )
        self.client.login(username="translator", password="Testpass123!")
        response = self.client.get(f"/file/{pf.uuid}")
        self.assertEqual(response.status_code, 200)

    @patch("kaplancloudapp.models.NewFileThread")
    def test_editor_context_has_can_edit(self, mock_thread):
        mock_thread.return_value.run = MagicMock()
        pf = ProjectFile.objects.create(name="e.xliff", project=self.project, status=4)
        self.client.login(username="pm", password="Testpass123!")
        response = self.client.get(f"/file/{pf.uuid}")
        self.assertIn("can_edit", response.context)

    @patch("kaplancloudapp.models.NewFileThread")
    def test_add_comment(self, mock_thread):
        mock_thread.return_value.run = MagicMock()
        pf = ProjectFile.objects.create(name="e.xliff", project=self.project, status=4)
        Segment.objects.create(tu_id=1, s_id=1, source="hello", file=pf)
        self.client.login(username="pm", password="Testpass123!")
        response = self.client.post(
            f"/file/{pf.uuid}",
            {"task": "add_comment", "comment": "Great!", "segment_id": "1"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.count(), 1)
        data = response.json()
        self.assertEqual(data["comment"], "Great!")

    @patch("kaplancloudapp.models.NewFileThread")
    def test_advance_file_status(self, mock_thread):
        mock_thread.return_value.run = MagicMock()
        pf = ProjectFile.objects.create(name="e.xliff", project=self.project, status=4)
        self.client.login(username="pm", password="Testpass123!")
        response = self.client.post(f"/file/{pf.uuid}", {"task": "advance_file_status"})
        self.assertEqual(response.status_code, 200)
        pf.refresh_from_db()
        self.assertEqual(pf.status, 5)

    @patch("kaplancloudapp.models.NewFileThread")
    def test_advance_file_status_forbidden_without_edit(self, mock_thread):
        mock_thread.return_value.run = MagicMock()
        reviewer = User.objects.create_user("reviewer", password="Testpass123!")
        pf = ProjectFile.objects.create(
            name="e.xliff",
            project=self.project,
            status=4,
            reviewer=reviewer,
        )
        self.client.login(username="reviewer", password="Testpass123!")
        response = self.client.post(f"/file/{pf.uuid}", {"task": "advance_file_status"})
        self.assertEqual(response.status_code, 403)


class ReportViewTests(TestCase):
    def setUp(self):
        en, fr = _make_languages()
        self.user = _pm_user()
        self.project = _make_project(self.user, en, fr)

    def test_login_required(self):
        report = ProjectReport.objects.create(
            project=self.project,
            content={"Total": {"words": 100}},
            status=3,
        )
        response = self.client.get(f"/report/{report.uuid}")
        self.assertEqual(response.status_code, 302)

    def test_get_status_json(self):
        report = ProjectReport.objects.create(
            project=self.project,
            content={"Total": {"words": 100}},
            status=3,
        )
        self.client.login(username="pm", password="Testpass123!")
        response = self.client.get(f"/report/{report.uuid}", {"task": "get_status"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], 3)

    def test_report_renders_template(self):
        report = ProjectReport.objects.create(
            project=self.project,
            content={
                "Total": {"words": 100},
                "file.xliff": {"words": 100},
            },
            status=3,
        )
        self.client.login(username="pm", password="Testpass123!")
        response = self.client.get(f"/report/{report.uuid}")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "report.html")
        self.assertIn("total", response.context)
        self.assertIn("files", response.context)
