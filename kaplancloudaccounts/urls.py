from django.urls import path

from . import views

urlpatterns = [
    path('change-password', views.change_password, name='change-password'),
    path('login', views.signin, name='login'),
    path('logout', views.signout, name='logout'),
    path('register', views.signup, name='register'),
]
