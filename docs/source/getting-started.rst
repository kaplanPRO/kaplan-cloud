Getting started
===============

Kaplan Cloud uses invitation tokens rather than open registration. Your
administrator generates a single-use ``UserRegistrationToken`` for you
and sends you a registration URL containing the token. The token also
determines your role (translator, reviewer, PM, or admin) — you don't
choose this yourself at sign-up.

Register
--------

1. Open the registration URL from your administrator. It looks like::

      https://your-instance.example.com/accounts/register?token=<TOKEN>

2. Choose a username and password and submit the form. The token field
   is filled in for you from the URL.

   .. image:: ./_static/img/user-registration-form.png
      :alt: Registration form

3. Once registration succeeds, you'll land on the login page. Sign in
   with the credentials you just created.

The token is single-use and cannot be reused after you register. If
something goes wrong during registration, ask your administrator to
issue you a fresh token.

Log in and log out
------------------

- Log in at ``/accounts/login``.
- Log out at ``/accounts/logout``. Logging out also fires when you
  change your password (see below).

Change your password
--------------------

Visit ``/accounts/change-password`` while logged in, enter your current
password and a new one, then submit. You will be signed out
automatically and will need to log in again with the new password.
