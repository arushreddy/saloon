"""
Tests for payments app.
Run with: python manage.py test payments
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date, timedelta
from accounts.models import User
from services.models import Service
from bookings.models import Booking
from .models import Payment


def make_user(phone='9876543210'):
    return User.objects.create_user(phone=phone)


def make_service():
    return Service.objects.create(
        name='Haircut', description='Test', price=500,
        duration_minutes=60, is_active=True
    )


def auth_client(user):
    from rest_framework_simplejwt.tokens import RefreshToken
    client = APIClient()
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(token.access_token)}')
    return client


def make_booking(user, service, booking_id='SB-PAY001'):
    return Booking.objects.create(
        user=user, service=service,
        date=date.today() + timedelta(days=1),
        time_slot=10, status='pending',
        booking_id=booking_id
    )


class CreateOrderTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.service = make_service()
        self.client = auth_client(self.user)
        self.booking = make_booking(self.user, self.service)

    def test_create_order_success(self):
        res = self.client.post(reverse('create-order'), {'booking_id': 'SB-PAY001'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('order_id', res.data)
        self.assertIn('amount', res.data)
        self.assertEqual(res.data['amount'], 50000)  # ₹500 = 50000 paise

    def test_create_order_wrong_user(self):
        other_user = make_user(phone='1112223334')
        other_client = auth_client(other_user)
        res = other_client.post(reverse('create-order'), {'booking_id': 'SB-PAY001'})
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_order_nonexistent_booking(self):
        res = self.client.post(reverse('create-order'), {'booking_id': 'SB-FAKE999'})
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_create_order_for_paid_booking(self):
        Payment.objects.create(
            user=self.user, booking=self.booking,
            amount=500, status='paid',
            razorpay_order_id='order_paid_123'
        )
        self.booking.status = 'confirmed'
        self.booking.save()
        # Re-fetch as pending booking — this should 404 since status is confirmed
        res = self.client.post(reverse('create-order'), {'booking_id': 'SB-PAY001'})
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)


class VerifyPaymentTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.service = make_service()
        self.booking = make_booking(self.user, self.service)
        self.payment = Payment.objects.create(
            user=self.user, booking=self.booking,
            amount=500, status='created',
            razorpay_order_id='order_dev_abc123'
        )
        self.client = auth_client(self.user)

    def test_dev_payment_verification_success(self):
        """
        FIX #3 REGRESSION TEST:
        Dev mode should only accept order IDs starting with 'order_dev_'.
        """
        res = self.client.post(reverse('verify-payment'), {
            'razorpay_order_id': 'order_dev_abc123',
            'razorpay_payment_id': 'pay_dev_12345',
            'razorpay_signature': 'dev_signature',
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.payment.refresh_from_db()
        self.booking.refresh_from_db()
        self.assertEqual(self.payment.status, 'paid')
        self.assertEqual(self.booking.status, 'confirmed')

    def test_real_order_id_rejected_without_keys(self):
        """Real Razorpay order ID must not be accepted in dev mode."""
        self.payment.razorpay_order_id = 'order_real123abc'
        self.payment.save()
        res = self.client.post(reverse('verify-payment'), {
            'razorpay_order_id': 'order_real123abc',
            'razorpay_payment_id': 'pay_test_123',
            'razorpay_signature': 'fake_sig',
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_double_verification_rejected(self):
        """Already-paid payment must not be processed twice."""
        self.payment.status = 'paid'
        self.payment.save()
        res = self.client.post(reverse('verify-payment'), {
            'razorpay_order_id': 'order_dev_abc123',
            'razorpay_payment_id': 'pay_dev_12345',
            'razorpay_signature': 'dev_signature',
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already verified', res.data['error'])

    def test_payment_status_endpoint(self):
        res = self.client.get(reverse('payment-status', args=['SB-PAY001']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['status'], 'created')


# ─────────────────────────────────────────────
# services/tests.py content inlined here
# ─────────────────────────────────────────────

from services.models import Service as Svc
from services.serializers import ServiceListSerializer


class ServiceListTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        Svc.objects.create(name='Active', description='x', price=100, is_active=True)
        Svc.objects.create(name='Inactive', description='x', price=200, is_active=False)

    def test_public_only_sees_active(self):
        res = self.client.get(reverse('list-services'))
        names = [s['name'] for s in res.data]
        self.assertIn('Active', names)
        self.assertNotIn('Inactive', names)

    def test_admin_sees_inactive_with_flag(self):
        admin = User.objects.create_user(phone='9990001111')
        admin.is_admin = True
        admin.save()
        c = auth_client(admin)
        res = c.get(reverse('list-services') + '?all=true')
        names = [s['name'] for s in res.data]
        self.assertIn('Inactive', names)

    def test_non_admin_cannot_see_all(self):
        """FIX #5: Regular user with ?all=true should still only see active."""
        user = User.objects.create_user(phone='8880001111')
        c = auth_client(user)
        res = c.get(reverse('list-services') + '?all=true')
        names = [s['name'] for s in res.data]
        self.assertNotIn('Inactive', names)

    def test_filter_by_category(self):
        Svc.objects.create(name='Facial', description='x', price=300, is_active=True, category='Skin')
        res = self.client.get(reverse('list-services') + '?category=skin')  # Case insensitive
        names = [s['name'] for s in res.data]
        self.assertIn('Facial', names)
        self.assertNotIn('Active', names)


class AdminServiceCRUDTest(TestCase):

    def setUp(self):
        self.admin = User.objects.create_user(phone='9990001112')
        self.admin.is_admin = True
        self.admin.save()
        self.client = auth_client(self.admin)

    def test_admin_can_create_service(self):
        res = self.client.post(reverse('create-service'), {
            'name': 'New Service', 'description': 'Desc',
            'price': '750', 'duration_minutes': 45,
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Svc.objects.filter(name='New Service').exists())

    def test_non_admin_cannot_create_service(self):
        regular = User.objects.create_user(phone='8880001112')
        c = auth_client(regular)
        res = c.post(reverse('create-service'), {
            'name': 'Hack', 'description': 'x', 'price': '100',
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_deactivate_service(self):
        svc = Svc.objects.create(name='Del Me', description='x', price=100, is_active=True)
        res = self.client.delete(reverse('delete-service', args=[svc.pk]))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        svc.refresh_from_db()
        self.assertFalse(svc.is_active)

    def test_cannot_deactivate_already_inactive(self):
        svc = Svc.objects.create(name='Already Off', description='x', price=100, is_active=False)
        res = self.client.delete(reverse('delete-service', args=[svc.pk]))
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)