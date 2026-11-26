import hashlib
import logging
from functools import wraps

from django.conf import settings
from django.contrib.auth import get_user_model, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.encoding import force_str
from django.utils.http import url_has_allowed_host_and_scheme, urlsafe_base64_decode
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    AccountInformationForm,
    ChangePasswordForm,
    ForgotPasswordForm,
    LoginForm,
    PasswordResetConfirmForm,
    SignUpForm,
)
from .models import PasswordResetToken
from .services import send_password_reset_email


User = get_user_model()
logger = logging.getLogger(__name__)


def guest_only(view_func):
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapped_view


def get_post_auth_redirect(request):
    redirect_to = request.POST.get('next') or request.GET.get('next')
    if redirect_to and url_has_allowed_host_and_scheme(
        url=redirect_to,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(redirect_to)
    return redirect('home')


def render_auth_form(request, form, title, submit_label, description=''):
    return render(request, 'authentication/form.html', {
        'form': form,
        'title': title,
        'submit_label': submit_label,
        'description': description,
    })


@guest_only
def sign_up(request):
    form = SignUpForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        return get_post_auth_redirect(request)
    return render_auth_form(
        request,
        form,
        'Create your account',
        'Sign up',
        'Create an account to save your microscopy work.',
    )


@guest_only
def log_in(request):
    form = LoginForm(
        request.POST if request.method == 'POST' else None,
        request=request,
    )
    if request.method == 'POST' and form.is_valid():
        login(request, form.user)
        return get_post_auth_redirect(request)
    return render_auth_form(
        request,
        form,
        'Welcome back',
        'Log in',
        'Sign in to continue to Cell Counter.',
    )


@require_POST
@login_required
def log_out(request):
    logout(request)
    return redirect('home')


@login_required
def change_account_information(request):
    form = AccountInformationForm(
        request.POST if request.method == 'POST' else None,
        instance=request.user,
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        return render(request, 'authentication/message.html', {
            'title': 'Account updated',
            'message': 'Your account information has been updated.',
        })
    return render_auth_form(
        request,
        form,
        'Account information',
        'Save changes',
    )


@login_required
def change_password(request):
    form = ChangePasswordForm(
        request.POST if request.method == 'POST' else None,
        user=request.user,
    )
    if request.method == 'POST' and form.is_valid():
        request.user.set_password(form.cleaned_data['new_password1'])
        request.user.save(update_fields=['password'])
        update_session_auth_hash(request, request.user)
        return render(request, 'authentication/message.html', {
            'title': 'Password changed',
            'message': 'Your password has been changed.',
        })
    return render_auth_form(
        request,
        form,
        'Change password',
        'Change password',
    )


@guest_only
def forgot_password(request):
    form = ForgotPasswordForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        send_password_reset_email(request, form.cleaned_data['email'])
        return render(request, 'authentication/message.html', {
            'title': 'Check your email',
            'message': 'If an account exists for that email, password reset instructions have been sent.',
        })
    return render_auth_form(
        request,
        form,
        'Forgot password',
        'Send reset link',
        'Enter the email address associated with your account.',
    )


def get_valid_password_reset_token(uidb64, token, *, lock=False):
    try:
        user_id = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=user_id)
    except (TypeError, ValueError, OverflowError):
        return None, 'malformed_user_reference'
    except User.DoesNotExist:
        return None, 'user_reference_not_found'

    if not user.is_active:
        return None, 'user_inactive'

    token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
    tokens = PasswordResetToken.objects.select_related('user')
    if lock:
        tokens = tokens.select_for_update()
    reset_token = tokens.filter(
        user=user,
        token_hash=token_hash,
    ).first()
    if reset_token is None:
        if PasswordResetToken.objects.filter(user=user).exists():
            return None, 'token_does_not_match_saved_record'
        return None, 'no_reset_token_record_for_user'
    if reset_token.used_at is not None:
        return None, 'token_already_used'
    if reset_token.expires_at <= timezone.now():
        return None, 'token_expired'
    if reset_token.password_hash != reset_token.user.password:
        return None, 'password_changed_since_request'
    return reset_token, None


def invalid_password_reset_response(request, reason):
    logger.warning('Password reset rejected (%s).', reason)
    context = {
        'title': 'Invalid reset link',
        'message': 'This password reset link is invalid or has expired.',
        'action_url': reverse('account:forgot_password'),
        'action_label': 'Request a new reset link',
    }
    if settings.DEBUG:
        context['diagnostic'] = reason
    return render(request, 'authentication/message.html', context, status=400)


@guest_only
def password_reset_confirm(request, uidb64, token):
    reset_token, invalid_reason = get_valid_password_reset_token(uidb64, token)
    if reset_token is None:
        return invalid_password_reset_response(request, invalid_reason)

    form = PasswordResetConfirmForm(
        request.POST if request.method == 'POST' else None,
        user=reset_token.user,
    )
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            reset_token, invalid_reason = get_valid_password_reset_token(
                uidb64,
                token,
                lock=True,
            )
            if reset_token is None:
                return invalid_password_reset_response(request, invalid_reason)
            user = reset_token.user
            user.set_password(form.cleaned_data['new_password1'])
            user.save(update_fields=['password'])
            PasswordResetToken.objects.filter(
                user=user,
                used_at__isnull=True,
            ).update(used_at=timezone.now())
        return render(request, 'authentication/message.html', {
            'title': 'Password reset',
            'message': 'Your password has been reset. You can now log in.',
        })
    return render_auth_form(
        request,
        form,
        'Choose a new password',
        'Reset password',
    )
