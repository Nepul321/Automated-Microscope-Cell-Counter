from django.contrib.auth import get_user_model, password_validation
from rest_framework import serializers


User = get_user_model()


class AccountInformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')

    def validate_email(self, value):
        matching_users = User.objects.filter(email__iexact=value)
        if self.instance is not None:
            matching_users = matching_users.exclude(pk=self.instance.pk)
        if matching_users.exists():
            raise serializers.ValidationError('A user with that email already exists.')
        return value


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)
    password_confirm = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        user = self.context['user']
        if not user.check_password(attrs['old_password']):
            raise serializers.ValidationError({'old_password': 'The current password is incorrect.'})
        if attrs['new_password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})

        password_validation.validate_password(attrs['new_password'], user=user)
        return attrs


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
