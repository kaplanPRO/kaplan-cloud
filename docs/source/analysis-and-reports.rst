Analysis and reports
====================

Project analysis estimates how much work a project contains: total
words, segments, and how many of them are already covered by existing
translation memories (exact and fuzzy matches). PMs trigger analyses
from the project page; results are saved as **reports** that can be
viewed later.

This page is for project managers and administrators.

Run an analysis
---------------

1. Open the project at ``/project/<uuid>``.
2. Right-click the file table (or use the dedicated action button) and
   pick **Analyze**. You can analyze the selected files or the whole
   project if no files are ticked.
3. A new row appears at the top of the **Reports** section in
   **Ready for Processing** state.

The Reports table
-----------------

The Reports section on the project page lists every analysis ever run
for the project, newest first. Each row has a live status badge:

- **Blank** — created but not yet queued.
- **Ready for Processing** — queued, waiting for the worker.
- **Processing** — actively being computed.
- **Complete** — ready to view.

The page polls the server every few seconds and updates the badge in
place as the analysis advances; you don't need to refresh manually.
(New in v0.6.0 — previously the page had to be reloaded.)

When a report reaches **Complete**, click its row to open it at
``/report/<uuid>``.

Reading a report
----------------

A completed report lists, per file:

- Total words and segments.
- Exact-match counts from each attached translation memory.
- Fuzzy-match buckets (e.g. 99–95%, 94–85%, 84–75%) and how many
  segments fall into each.
- New words — those without any TM match.

PMs typically use this breakdown to estimate translation effort, quote
clients, and decide which files (if any) warrant pre-translation from
TM.

Downloading files
-----------------

When work is complete, the file table on the project page lets you
download the translated output of each file individually, or export
the entire project as an archive. Choose the export action from the
right-click menu or the action buttons on the file row.
