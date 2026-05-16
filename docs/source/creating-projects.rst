Creating projects
=================

This page is for **project managers** (members of the ``PM`` group) and
administrators. If you're a translator or reviewer, you'll receive
projects from a PM and won't see these screens.

Create a project
----------------

1. From the project list, click the **Create** button to open the new
   project form at ``/project/new``.

   .. image:: ./_static/img/project-form.png
      :alt: New project form

2. Fill in the project metadata:

   - **Name** and **due date**.
   - **Client** — pick from existing clients, or create one ahead of
     time from the Django admin.
   - **Source language** and one or more **target languages** — these
     are :doc:`language profiles <language-profiles>` that an admin
     has set up.
   - **Translation memories** to attach to the project. Optional;
     attached TMs will surface as matches in the editor.

3. Upload your files. Kaplan Cloud accepts:

   - **Source files** in the formats supported by the underlying
     ``kaplan`` library (e.g. ``.docx``, ``.xlsx``, ``.xliff``).
   - **Bilingual files** for projects that already contain translation
     work-in-progress (the source-language text is paired with a
     partially-filled target).
   - **Reference files** — style guides, glossaries, brand assets —
     downloadable from the project page but not opened in the editor.

4. Submit. Each uploaded file is processed in the background and the
   project moves through **Preparing** → **Ready for Analysis** →
   **Analyzing** → **Ready for Translation**. Watch the project page
   while this happens; the file rows light up as each file is ready.

Assign linguists
----------------

Once a project is **Ready for Translation**, assign a translator (and
optionally a reviewer) to each file.

1. On the project page, tick the checkboxes for the files you want to
   assign. Leaving all rows unticked applies the next action to every
   file.

2. Right-click anywhere on the file table and pick **Assign
   translator** or **Assign reviewer**.

   .. image:: ./_static/img/files-context-menu.png
      :alt: Files context menu

3. Enter the username of the linguist and submit.

   .. image:: ./_static/img/assign-team-member-form.png
      :alt: Assign team member form

   .. image:: ./_static/img/team-member-assigned.png
      :alt: Team member assigned

Once assigned, the linguist sees the project in their own project list
and can open the file in the :doc:`editor`. The file status moves to
**In Translation** the first time they open it.
