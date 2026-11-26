from django.urls import path
from django.views.generic.base import RedirectView
from rest_framework.authtoken.views import obtain_auth_token

from . import views


app_name = 'authentication_api'

urlpatterns = [
    path('token/', obtain_auth_token, name='token'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('change-password/', views.change_password, name='change_password'),
    path('account/', views.change_account_information, name='change_account_information'),
    path(
        'password-reset-confirm/<uidb64>/<token>/',
        RedirectView.as_view(
            pattern_name='account:password_reset_confirm',
            permanent=False,
        ),
        name='legacy_password_reset_confirm',
    ),
]
