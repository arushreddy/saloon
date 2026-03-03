"""
Tests for accounts app: OTP flow, JWT auth, profile management.
Run with: python manage.py test accounts
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch
from django.utils import timezone
from datetime import timedelta
from .models import User, OTP


class NormalizePhoneTest(TestCase):
    """Test phone normalization used in views."""

    def test_strips_plus91(self):
        from .views import normalize_phone
        self.assertEqual(normalize_phone('+919876543210'), '9876543210')

    def test_strips_91_prefix(self):
        from .views import normalize_phone
        self.assertEqual(normalize_phone('919876543210'), '9876543210')

    def test_strips_spaces_dashes(self):
        from .views import normalize_phone
        self.assertEqual(normalize_phone('98765 43210'), '9876543210')
        self.assertEqual(normalize_phone('98765-43210'), '9876543210')

    def test_plain_number_unchanged(self):
        from .views import normalize_phone
        self.assertEqual(normalize_phone('9876543210'), '9876543210')


class SendOTPTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = reverse('send-otp')

    def test_send_otp_success(self):
        res = self.client.post(self.url, {'phone': '9876543210'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('otp_debug', res.data)  # DEBUG=True in test env
        self.assertTrue(OTP.objects.filter(phone='9876543210').exists())

    def test_send_otp_invalid_phone(self):
        res = self.client.post(self.url, {'phone': '123'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_send_otp_rate_limit(self):
        """After 5 OTPs in an hour, should get 429."""
        for _ in range(5):
            OTP.objects.create(phone='9876543210', otp='123456')
        res = self.client.post(self.url, {'phone': '9876543210'})
        self.assertEqual(res.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_send_otp_normalizes_plus91(self):
        """Phone with +91 prefix should be stored as 10 digits."""
        res = self.client.post(self.url, {'phone': '+919876543210'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['phone'], '9876543210')


class VerifyOTPTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = reverse('verify-otp')
        self.phone = '9876543210'

    def _create_otp(self, otp_code='123456', expired=False):
        otp = OTP.objects.create(phone=self.phone, otp=otp_code)
        if expired:
            # Manually expire by setting created_at to 10 mins ago
            OTP.objects.filter(pk=otp.pk).update(
                created_at=timezone.now() - timedelta(minutes=10)
            )
        return otp

    def test_verify_correct_otp(self):
        self._create_otp('654321')
        res = self.client.post(self.url, {'phone': self.phone, 'otp': '654321'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', res.data)
        self.assertIn('access', res.data['tokens'])
        self.assertIn('refresh', res.data['tokens'])

    def test_verify_wrong_otp_decrements_attempts(self):
        self._create_otp('654321')
        res = self.client.post(self.url, {'phone': self.phone, 'otp': '000000'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('2 attempts remaining', res.data['error'])

    def test_verify_expired_otp(self):
        self._create_otp('654321', expired=True)
        res = self.client.post(self.url, {'phone': self.phone, 'otp': '654321'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('expired', res.data['error'].lower())

    def test_verify_otp_max_attempts_blocks(self):
        """
        FIX #1 REGRESSION TEST:
        After 3 wrong attempts, should show "too many attempts" not "0 remaining".
        """
        otp = self._create_otp('654321')
        for _ in range(3):
            self.client.post(self.url, {'phone': self.phone, 'otp': '000000'})
        # 4th attempt should be blocked
        res = self.client.post(self.url, {'phone': self.phone, 'otp': '654321'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('too many attempts', res.data['error'].lower())

    def test_verify_creates_new_user(self):
        self._create_otp('123456')
        res = self.client.post(self.url, {'phone': self.phone, 'otp': '123456'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['is_new_user'])
        self.assertTrue(User.objects.filter(phone=self.phone).exists())

    def test_verify_existing_user_not_recreated(self):
        User.objects.create_user(phone=self.phone)
        self._create_otp('123456')
        res = self.client.post(self.url, {'phone': self.phone, 'otp': '123456'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(res.data['is_new_user'])
        self.assertEqual(User.objects.filter(phone=self.phone).count(), 1)

    def test_verify_no_otp_found(self):
        res = self.client.post(self.url, {'phone': self.phone, 'otp': '123456'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class ProfileTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(phone='9876543210', name='Test User')

    def _auth(self):
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')

    def test_get_profile_authenticated(self):
        self._auth()
        res = self.client.get(reverse('get-profile'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['phone'], '9876543210')

    def test_get_profile_unauthenticated(self):
        res = self.client.get(reverse('get-profile'))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_profile(self):
        self._auth()
        res = self.client.put(reverse('update-profile'), {'name': 'New Name', 'email': 'test@test.com'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, 'New Name')
        self.assertEqual(self.user.email, 'test@test.com')

    def test_cannot_change_phone_via_profile(self):
        """Phone should be read-only."""
        self._auth()
        res = self.client.put(reverse('update-profile'), {'phone': '1111111111'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone, '9876543210')  # Unchanged