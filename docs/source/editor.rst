The translation editor
======================

The editor at ``/file/<uuid>`` is where translators and reviewers work
through a file segment by segment. You can reach it from the file row
on a project page.

Segments and statuses
---------------------

Each segment has a source-language text and a target-language text you
edit. A segment moves through three statuses:

- **Blank** — untouched.
- **Draft** — you have entered or modified the target text but haven't
  finalized it.
- **Translated** — you have confirmed the segment.

Saving a target text marks the segment as Draft. Confirming a segment
moves it to Translated. A file becomes eligible to move to **In
Review** once all of its segments are Translated.

Translation memory matches
--------------------------

When the project's PM attached one or more translation memories to the
project, the editor looks up each source segment against them and
displays match candidates alongside the segment. Matches can be
**exact** (100% identical source text) or **fuzzy** (similar but not
identical, ranked by similarity score). Selecting a match copies its
target text into the current segment, ready for you to confirm or
edit.

For more on how TMs are created and what data they contain, see
:doc:`translation-memories`.

Comments
--------

You can leave a comment on any segment — useful for flagging a tricky
choice for the reviewer, or for the reviewer to push something back to
the translator. Comments stay attached to the segment as the file
moves through the workflow.

Translator vs. reviewer mode
----------------------------

A file in **In Translation** status (after a translator has opened it)
is editable by its assigned translator. Once the translator finishes,
the file moves to **In Review** and the assigned reviewer takes over
in the same editor view; the reviewer can edit segments and either
push them back to Draft (returning the file to translation) or
confirm them as final.

PMs and project owners can open and edit any file at any phase. Other
users cannot edit a file they are not assigned to.
