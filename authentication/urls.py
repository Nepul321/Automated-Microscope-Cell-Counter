from django.urls import path

from . import views


app_name = 'account'

urlpatterns = [
    path('sign-up/', views.sign_up, name='sign_up'),
    path('login/', views.log_in, name='login'),
    path('logout/', views.log_out, name='logout'),
    path('account/', views.change_account_information, name='account_information'),
    path('change-password/', views.change_password, name='change_password'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path(
        'password-reset-confirm/<uidb64>/<token>/',
        views.password_reset_confirm,
        name='password_reset_confirm',
    ),
]
