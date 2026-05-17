Language profiles
=================

A **language profile** represents a language Kaplan Cloud knows about.
Projects, translation memories, and termbases all reference language
profiles, so every language you want to translate from or into needs
one before you can use it.

A language profile carries:

- A human-readable **name** (e.g. *English (United States)*).
- An **ISO code** — usually a BCP-47 tag like ``en-US``, ``fr``, or
  ``ar-EG``. This is the profile's primary key.
- A **directionality** flag (left-to-right or right-to-left) used by
  the editor to render the script correctly.

Who can manage language profiles
--------------------------------

Language profiles are managed by administrators (and members of the
``PM`` group) from the Django admin at ``/admin/`` — they are not
exposed in the regular browser navigation.

Add a language profile
----------------------

1. Sign in to the Django admin at ``/admin/``. From the left-hand
   sidebar, find **Language profiles** and click **Add language
   profile**.

   .. image:: ./_static/img/language-profile.png
      :alt: Language profiles admin

2. Enter the language **name**, **ISO code**, and the direction flag,
   then save.

   .. image:: ./_static/img/language-profile-form.png
      :alt: Language profile form

The new profile becomes available immediately as a source or target
language when creating projects and TMs.
