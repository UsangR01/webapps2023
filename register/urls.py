"""
register/urls.py
"""

from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("logout/", views.logout_user, name="logout"),
    path("login/", views.login_user, name="login"),
    path("register/", views.register_user, name="register"),
    path("password_reset/", auth_views.PasswordResetView.as_view(template_name="register/password_reset.html"), name="password_reset"),
    path('social-auth/', include('social_django.urls', namespace='social')),
    path('facebook/callback/', views.facebook_callback, name='facebook_callback'),
]
