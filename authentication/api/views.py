from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from ..services import send_password_reset_email
from .serializers import (
    AccountInformationSerializer,
    ForgotPasswordSerializer,
    PasswordChangeSerializer,
)


@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    serializer = ForgotPasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    send_password_reset_email(request, serializer.validated_data['email'])
    return Response({
        'detail': 'If an account exists for that email, password reset instructions have been sent.',
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    serializer = PasswordChangeSerializer(
        data=request.data,
        context={'user': request.user},
    )
    serializer.is_valid(raise_exception=True)
    user = request.user
    user.set_password(serializer.validated_data['new_password'])
    user.save(update_fields=['password'])
    return Response({'detail': 'Password changed successfully.'})


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def change_account_information(request):
    serializer = AccountInformationSerializer(
        request.user,
        data=request.data,
        partial=True,
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)
