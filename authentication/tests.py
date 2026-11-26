from urllib.parse import urlsplit

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import Client, TestCase, override_settings
from django.urls import resolve, reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.test import APIClient


User = get_user_model()


class AuthenticationPageTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_sign_up_creates_user_and_starts_session(self):
        response = self.client.post(reverse('account:sign_up'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'Unique-Test-Passphrase-984!',
            'password2': 'Unique-Test-Passphrase-984!',
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())
        account_response = self.client.get(reverse('account:account_information'))
        self.assertEqual(account_response.status_code, 200)

    def test_guest_only_pages_redirect_authenticated_users(self):
        user = User.objects.create_user(
            username='guestblocked',
            password='Unique-Test-Passphrase-984!',
        )
        self.client.force_login(user)

        for page_name in ('account:sign_up', 'account:login', 'account:forgot_password'):
            response = self.client.get(reverse(page_name))
            self.assertRedirects(response, reverse('home'))

    def test_logged_in_only_pages_redirect_guests(self):
        for page_name in ('account:account_information', 'account:change_password'):
            response = self.client.get(reverse(page_name))
            self.assertRedirects(
                response,
                f"{reverse('account:login')}?next={reverse(page_name)}",
            )

    def test_login_returns_user_to_requested_protected_page(self):
        user = User.objects.create_user(
            username='returnuser',
            password='Unique-Test-Passphrase-984!',
        )
        protected_url = reverse('account:change_password')
        login_url = f"{reverse('account:login')}?next={protected_url}"

        page_response = self.client.get(protected_url)
        login_page = self.client.get(page_response.url)
        self.assertContains(login_page, f'value="{protected_url}"')

        login_response = self.client.post(login_url, {
            'username': user.username,
            'password': 'Unique-Test-Passphrase-984!',
            'next': protected_url,
        })

        self.assertRedirects(login_response, protected_url)
        self.assertEqual(self.client.get(protected_url).status_code, 200)

    def test_login_uses_home_for_external_next_target(self):
        user = User.objects.create_user(
            username='safeuser',
            password='Unique-Test-Passphrase-984!',
        )

        response = self.client.post(
            f"{reverse('account:login')}?next=https://attacker.example",
            {
                'username': user.username,
                'password': 'Unique-Test-Passphrase-984!',
                'next': 'https://attacker.example',
            },
        )

        self.assertRedirects(response, reverse('home'))

    def test_home_separates_guest_and_member_upload_access(self):
        guest_response = self.client.get(reverse('home'))
        self.assertContains(guest_response, 'Sign in to analyze an image')
        self.assertNotContains(guest_response, 'Microscopy image')

        user = User.objects.create_user(
            username='member',
            password='Unique-Test-Passphrase-984!',
        )
        self.client.force_login(user)
        member_response = self.client.get(reverse('home'))
        self.assertContains(member_response, 'Microscopy image')
        self.assertNotContains(member_response, 'Sign in to analyze an image')

    def test_custom_login_change_password_and_logout_pages(self):
        user = User.objects.create_user(
            username='existing',
            password='Unique-Test-Passphrase-984!',
        )

        login_response = self.client.post(reverse('account:login'), {
            'username': user.username,
            'password': 'Unique-Test-Passphrase-984!',
        })
        self.assertEqual(login_response.status_code, 302)

        change_response = self.client.post(reverse('account:change_password'), {
            'old_password': 'Unique-Test-Passphrase-984!',
            'new_password1': 'Another-Unique-Passphrase-876!',
            'new_password2': 'Another-Unique-Passphrase-876!',
        })
        self.assertEqual(change_response.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.check_password('Another-Unique-Passphrase-876!'))

        logout_response = self.client.post(reverse('account:logout'))
        self.assertEqual(logout_response.status_code, 302)
        self.assertRedirects(
            self.client.get(reverse('account:account_information')),
            f"{reverse('account:login')}?next={reverse('account:account_information')}",
        )

    def test_account_information_form_updates_user(self):
        user = User.objects.create_user(
            username='profileuser',
            email='profile@example.com',
            password='Unique-Test-Passphrase-984!',
        )
        self.client.force_login(user)

        response = self.client.post(reverse('account:account_information'), {
            'username': 'profileuser',
            'email': 'updated@example.com',
            'first_name': 'Cell',
            'last_name': 'Counter',
        })

        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.email, 'updated@example.com')
        self.assertEqual(user.first_name, 'Cell')

    def test_browser_login_requires_csrf(self):
        csrf_client = Client(enforce_csrf_checks=True)
        login_url = reverse('account:login')
        csrf_client.get(login_url)
        csrf_token = csrf_client.cookies['csrftoken'].value

        rejected = csrf_client.post(login_url, {
            'username': 'someone',
            'password': 'wrong',
        })
        accepted = csrf_client.post(
            login_url,
            {'username': 'someone', 'password': 'wrong'},
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(rejected.status_code, 403)
        self.assertEqual(accepted.status_code, 200)

    def test_forgot_password_email_contains_working_reset_link(self):
        user = User.objects.create_user(
            username='resetuser',
            email='reset@example.com',
            password='Unique-Test-Passphrase-984!',
        )

        with override_settings(ALLOWED_HOSTS=['localhost']):
            response = self.client.post(
                reverse('account:forgot_password'),
                {'email': user.email},
                HTTP_HOST='localhost:8000',
            )
        self.assertEqual(response.status_code, 200)
        self.client.post(reverse('account:forgot_password'), {'email': user.email})
        self.assertEqual(len(mail.outbox), 2)

        reset_urls = [
            next(line for line in message.body.splitlines() if line.startswith('http'))
            for message in mail.outbox
        ]
        reset_url = reset_urls[0]
        reset_path = urlsplit(reset_url).path
        newest_reset_path = urlsplit(reset_urls[1]).path
        reset_kwargs = resolve(reset_path).kwargs
        self.assertTrue(reset_path.startswith('/r/'))
        self.assertLessEqual(len(reset_url), 80)

        with override_settings(SECRET_KEY='rotated-development-secret'):
            legacy_response = self.client.get(
                reverse('authentication_api:legacy_password_reset_confirm', kwargs=reset_kwargs),
                follow=True,
            )
            self.assertEqual(legacy_response.status_code, 200)
            self.assertContains(legacy_response, 'Choose a new password')

            reset_page = self.client.get(reset_path)
            self.assertEqual(reset_page.status_code, 200)
            self.assertContains(reset_page, 'Choose a new password')

            reset_response = self.client.post(reset_path, {
                'new_password1': 'Reset-Unique-Passphrase-654!',
                'new_password2': 'Reset-Unique-Passphrase-654!',
            })
        self.assertEqual(reset_response.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.check_password('Reset-Unique-Passphrase-654!'))
        self.assertEqual(self.client.get(reset_path).status_code, 400)
        self.assertEqual(self.client.get(newest_reset_path).status_code, 400)

    def test_forgot_password_does_not_disclose_unknown_email(self):
        response = self.client.post(reverse('account:forgot_password'), {
            'email': 'missing@example.com',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)
        self.assertContains(response, 'If an account exists for that email')

    def test_invalid_reset_link_offers_retry_and_logs_safe_diagnostic(self):
        user = User.objects.create_user(
            username='invalidreset',
            email='invalidreset@example.com',
            password='Unique-Test-Passphrase-984!',
        )
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        invalid_url = reverse(
            'account:password_reset_confirm',
            kwargs={'uidb64': uidb64, 'token': 'invalid-token'},
        )

        with override_settings(DEBUG=True):
            with self.assertLogs('authentication.views', level='WARNING') as captured:
                response = self.client.get(invalid_url)

        self.assertEqual(response.status_code, 400)
        self.assertContains(response, 'Request a new reset link', status_code=400)
        self.assertContains(response, 'no_reset_token_record_for_user', status_code=400)
        self.assertIn('no_reset_token_record_for_user', captured.output[0])


class AuthenticationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.account_url = reverse('authentication_api:change_account_information')

    def test_token_authentication_works_for_cross_origin_api(self):
        user = User.objects.create_user(
            username='tokenuser',
            password='Unique-Test-Passphrase-984!',
        )
        token_response = self.client.post(reverse('authentication_api:token'), {
            'username': user.username,
            'password': 'Unique-Test-Passphrase-984!',
        })
        self.assertEqual(token_response.status_code, 200)

        token_client = APIClient()
        token_client.credentials(HTTP_AUTHORIZATION=f"Token {token_response.data['token']}")
        response = token_client.patch(
            self.account_url,
            {'first_name': 'Token'},
            HTTP_ORIGIN='https://external-frontend.example',
            HTTP_SEC_FETCH_SITE='cross-site',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['first_name'], 'Token')

    def test_api_forgot_password_sends_link_to_website_reset_page(self):
        user = User.objects.create_user(
            username='apireset',
            email='apireset@example.com',
            password='Unique-Test-Passphrase-984!',
        )

        response = self.client.post(
            reverse('authentication_api:forgot_password'),
            {'email': user.email},
            format='json',
            HTTP_ORIGIN='https://external-frontend.example',
            HTTP_SEC_FETCH_SITE='cross-site',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('If an account exists', response.data['detail'])
        self.assertEqual(len(mail.outbox), 1)
        reset_url = next(
            line for line in mail.outbox[0].body.splitlines()
            if line.startswith('http')
        )
        self.assertTrue(urlsplit(reset_url).path.startswith('/r/'))
        self.assertEqual(
            self.client.get(urlsplit(reset_url).path).status_code,
            200,
        )

    def test_session_authentication_is_same_origin_only_for_api(self):
        user = User.objects.create_user(
            username='sessionuser',
            password='Unique-Test-Passphrase-984!',
        )
        self.client.force_login(user)
        api_client = APIClient()
        api_client.cookies.update(self.client.cookies)

        same_origin_response = api_client.patch(
            self.account_url,
            {'first_name': 'SameOrigin'},
            HTTP_ORIGIN='http://testserver',
            HTTP_SEC_FETCH_SITE='same-origin',
        )
        cross_origin_response = api_client.patch(
            self.account_url,
            {'first_name': 'CrossOrigin'},
            HTTP_ORIGIN='https://external-frontend.example',
            HTTP_SEC_FETCH_SITE='cross-site',
        )

        self.assertEqual(same_origin_response.status_code, 200)
        self.assertEqual(cross_origin_response.status_code, 401)
