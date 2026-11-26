from django import forms
from django.contrib.auth import authenticate, get_user_model, password_validation
from django.core.exceptions import ValidationError


User = get_user_model()


class StyledFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


class SignUpForm(StyledFormMixin, forms.Form):
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password1 = forms.CharField(label='Password', strip=False, widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm password', strip=False, widget=forms.PasswordInput)

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError('A user with that username already exists.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('A user with that email already exists.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'Passwords do not match.')
        elif password1 and cleaned_data.get('username') and cleaned_data.get('email'):
            user = User(username=cleaned_data['username'], email=cleaned_data['email'])
            try:
                password_validation.validate_password(password1, user=user)
            except ValidationError as error:
                self.add_error('password1', error)
        return cleaned_data

    def save(self):
        return User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password1'],
        )


class LoginForm(StyledFormMixin, forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(strip=False, widget=forms.PasswordInput)

    def __init__(self, *args, request=None, **kwargs):
        self.request = request
        self.user = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        if username and password:
            self.user = authenticate(self.request, username=username, password=password)
            if self.user is None:
                raise ValidationError('The username or password is incorrect.')
        return cleaned_data


class AccountInformationForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')

    def clean_email(self):
        email = self.cleaned_data['email']
        matches = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if matches.exists():
            raise ValidationError('A user with that email already exists.')
        return email


class ChangePasswordForm(StyledFormMixin, forms.Form):
    old_password = forms.CharField(strip=False, widget=forms.PasswordInput)
    new_password1 = forms.CharField(label='New password', strip=False, widget=forms.PasswordInput)
    new_password2 = forms.CharField(label='Confirm new password', strip=False, widget=forms.PasswordInput)

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        old_password = cleaned_data.get('old_password')
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')
        if old_password and not self.user.check_password(old_password):
            self.add_error('old_password', 'The current password is incorrect.')
        if new_password1 and new_password2 and new_password1 != new_password2:
            self.add_error('new_password2', 'Passwords do not match.')
        elif new_password1:
            try:
                password_validation.validate_password(new_password1, user=self.user)
            except ValidationError as error:
                self.add_error('new_password1', error)
        return cleaned_data


class ForgotPasswordForm(StyledFormMixin, forms.Form):
    email = forms.EmailField()


class PasswordResetConfirmForm(StyledFormMixin, forms.Form):
    new_password1 = forms.CharField(label='New password', strip=False, widget=forms.PasswordInput)
    new_password2 = forms.CharField(label='Confirm new password', strip=False, widget=forms.PasswordInput)

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')
        if password1 and password2 and password1 != password2:
            self.add_error('new_password2', 'Passwords do not match.')
        elif password1:
            try:
                password_validation.validate_password(password1, user=self.user)
            except ValidationError as error:
                self.add_error('new_password1', error)
        return cleaned_data
