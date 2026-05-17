Inviting teammates
==================

Kaplan Cloud uses single-use **registration tokens** to onboard new
users. As an administrator, you generate a token for each prospective
user, choose what role they'll get on registration, and share the
resulting registration URL with them.

This page is for administrators.

Generate a token
----------------

1. Sign in to the Django admin at ``/admin/``. From the left-hand
   sidebar, find **User registration tokens** and click **Add user
   registration token**.

   .. image:: ./_static/img/user-registration-token-form.png
      :alt: New user registration token form

2. Pick the **user type** for the recipient (translator, reviewer, PM,
   or admin). On registration, the new user is automatically added to
   the matching group and granted the corresponding permissions.

3. (Optional) Pick a **client team** the new user will belong to.
   Members of a client team can see projects and translation memories
   scoped to that client.

4. Save the token. The token value is generated for you and is
   displayed on the token's detail page.

   .. image:: ./_static/img/user-registration-token.png
      :alt: User registration token detail

.. warning::

   Tokens are single-use, can no longer be edited once created, and
   the token field is read-only in the admin. Copy the value before
   you leave the page — if you lose it, you'll need to generate a
   fresh token.

Share the registration URL
--------------------------

Send the recipient a registration URL of the form::

   https://your-instance.example.com/accounts/register?token=<TOKEN>

When they open the URL and submit the registration form, the token is
consumed and the account is created with the role you chose. See
:doc:`getting-started` for the recipient's view of the same flow.
