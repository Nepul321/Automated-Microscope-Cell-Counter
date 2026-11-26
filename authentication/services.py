import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .models import PasswordResetToken


User = get_user_model()


def send_password_reset_email(request, email):
    for user in User.objects.filter(email__iexact=email, is_active=True):
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = secrets.token_urlsafe(32)
        now = timezone.now()
        PasswordResetToken.objects.filter(user=user).filter(
            Q(used_at__isnull=False) | Q(expires_at__lte=now)
        ).delete()
        PasswordResetToken.objects.create(
            user=user,
            token_hash=hashlib.sha256(token.encode('utf-8')).hexdigest(),
            password_hash=user.password,
            expires_at=now + timedelta(seconds=settings.PASSWORD_RESET_TIMEOUT),
        )
        reset_path = reverse(
            'password_reset_confirm_short',
            kwargs={'uidb64': uid, 'token': token},
        )
        reset_url = request.build_absolute_uri(reset_path)
        send_mail(
            'Password reset for Cell Counter',
            (
                'To reset your password, open the link below:\n\n'
                f'{reset_url}\n\n'
                'If you did not request a password reset, you can ignore this email.'
            ),
            None,
            [user.email],
        )
