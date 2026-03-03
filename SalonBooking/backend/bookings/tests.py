"""
Tests for bookings app: slot logic, overbooking prevention, concurrency.
Run with: python manage.py test bookings
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date, timedelta
from accounts.models import User
from services.models import Service
from .models import Booking, SlotConfig


def make_user(phone='9876543210'):
    return User.objects.create_user(phone=phone)


def make_service(name='Haircut', price=300):
    return Service.objects.create(
        name=name, description='Test service',
        price=price, duration_minutes=60, is_active=True
    )


def auth_client(user):
    from rest_framework_simplejwt.tokens import RefreshToken
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
    return client


class AvailableDatesTest(TestCase):

    def test_returns_30_days(self):
        client = APIClient()
        res = client.get(reverse('available-dates'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 30)

    def test_closed_date_shows_false(self):
        tomorrow = date.today() + timedelta(days=1)
        SlotConfig.objects.create(date=tomorrow, is_open=False)
        client = APIClient()
        res = client.get(reverse('available-dates'))
        tomorrow_data = next(d for d in res.data if d['date'] == str(tomorrow))
        self.assertFalse(tomorrow_data['is_open'])

    def test_uses_single_db_query(self):
        """Ensure we're not doing N+1 queries (30 queries for 30 days)."""
        from django.test.utils import CaptureQueriesContext
        from django.db import connection
        client = APIClient()
        with CaptureQueriesContext(connection) as ctx:
            client.get(reverse('available-dates'))
        # Should be 1 query for SlotConfig, not 30
        self.assertLessEqual(len(ctx.captured_queries), 3)


class AvailableSlotsTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.tomorrow = str(date.today() + timedelta(days=1))

    def test_returns_slots_for_open_date(self):
        res = self.client.get(reverse('available-slots'), {'date': self.tomorrow})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(len(res.data['slots']) > 0)
        self.assertTrue(res.data['is_open'])

    def test_returns_closed_for_closed_date(self):
        d = date.today() + timedelta(days=2)
        SlotConfig.objects.create(date=d, is_open=False)
        res = self.client.get(reverse('available-slots'), {'date': str(d)})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(res.data['is_open'])

    def test_rejects_past_dates(self):
        yesterday = str(date.today() - timedelta(days=1))
        res = self.client.get(reverse('available-slots'), {'date': yesterday})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rejects_invalid_date_format(self):
        res = self.client.get(reverse('available-slots'), {'date': '01-01-2026'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_slot_shows_booked_count(self):
        user = make_user()
        service = make_service()
        tomorrow = date.today() + timedelta(days=1)
        Booking.objects.create(
            user=user, service=service,
            date=tomorrow, time_slot=10,
            status='confirmed',
            booking_id='TEST-001'
        )
        res = self.client.get(reverse('available-slots'), {'date': str(tomorrow)})
        slot_10 = next(s for s in res.data['slots'] if s['hour'] == 10)
        self.assertEqual(slot_10['booked_count'], 1)

    def test_full_slot_shows_unavailable(self):
        tomorrow = date.today() + timedelta(days=1)
        service = make_service()
        for i in range(5):
            u = make_user(phone=f'98765432{i:02d}')
            Booking.objects.create(
                user=u, service=service,
                date=tomorrow, time_slot=11,
                status='confirmed',
                booking_id=f'TEST-{i:03d}'
            )
        res = self.client.get(reverse('available-slots'), {'date': str(tomorrow)})
        slot_11 = next(s for s in res.data['slots'] if s['hour'] == 11)
        self.assertFalse(slot_11['available'])
        self.assertEqual(slot_11['booked_count'], 5)


class CreateBookingTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.service = make_service()
        self.client = auth_client(self.user)
        self.tomorrow = date.today() + timedelta(days=1)

    def _book(self, time_slot=10, service_id=None, date=None):
        return self.client.post(reverse('create-booking'), {
            'service_id': service_id or self.service.pk,
            'date': str(date or self.tomorrow),
            'time_slot': time_slot,
        })

    def test_create_booking_success(self):
        res = self._book()
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn('booking_id', res.data['booking'])
        self.assertTrue(res.data['booking']['booking_id'].startswith('SB-'))

    def test_cannot_book_past_date(self):
        yesterday = date.today() - timedelta(days=1)
        res = self._book(date=yesterday)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_book_inactive_service(self):
        self.service.is_active = False
        self.service.save()
        res = self._book()
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_double_book_same_slot(self):
        self._book(time_slot=10)
        res = self._book(time_slot=10)  # Same user, same slot
        self.assertEqual(res.status_code, status.HTTP_409_CONFLICT)
        self.assertIn('already have a booking', res.data['error'])

    def test_overbooking_prevention(self):
        """
        FIX #2 REGRESSION TEST:
        6th booking attempt for a slot with max=5 must be rejected.
        """
        service = self.service
        tomorrow = self.tomorrow
        # Fill up the slot with 5 different users
        for i in range(5):
            u = make_user(phone=f'88765432{i:02d}')
            Booking.objects.create(
                user=u, service=service,
                date=tomorrow, time_slot=14,
                status='confirmed',
                booking_id=f'OVR-{i:03d}'
            )
        # 6th booking should fail
        res = self._book(time_slot=14)
        self.assertEqual(res.status_code, status.HTTP_409_CONFLICT)
        self.assertIn('fully booked', res.data['error'])

    def test_cancelled_booking_does_not_count_toward_slot(self):
        """Cancelled bookings should free up the slot."""
        service = self.service
        tomorrow = self.tomorrow
        for i in range(4):
            u = make_user(phone=f'77765432{i:02d}')
            Booking.objects.create(
                user=u, service=service,
                date=tomorrow, time_slot=15,
                status='confirmed',
                booking_id=f'CNF-{i:03d}'
            )
        # 5th is cancelled — slot should NOT be full
        u5 = make_user(phone='7776543299')
        Booking.objects.create(
            user=u5, service=service,
            date=tomorrow, time_slot=15,
            status='cancelled',  # Cancelled!
            booking_id='CNF-099'
        )
        res = self._book(time_slot=15)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_unauthenticated_cannot_book(self):
        anon = APIClient()
        res = anon.post(reverse('create-booking'), {
            'service_id': self.service.pk,
            'date': str(self.tomorrow),
            'time_slot': 10,
        })
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_time_slot_rejected(self):
        res = self._book(time_slot=3)  # Before 9 AM default opening
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_closed_date_cannot_be_booked(self):
        d = date.today() + timedelta(days=3)
        SlotConfig.objects.create(date=d, is_open=False)
        res = self._book(date=d)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('closed', res.data['error'])


class CancelBookingTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.service = make_service()
        self.client = auth_client(self.user)
        self.booking = Booking.objects.create(
            user=self.user, service=self.service,
            date=date.today() + timedelta(days=2),
            time_slot=10, status='confirmed',
            booking_id='SB-CANCEL01'
        )

    def test_cancel_confirmed_booking(self):
        res = self.client.post(reverse('cancel-booking', args=['SB-CANCEL01']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'cancelled')

    def test_cannot_cancel_already_cancelled(self):
        self.booking.status = 'cancelled'
        self.booking.save()
        res = self.client.post(reverse('cancel-booking', args=['SB-CANCEL01']))
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_cancel_completed_booking(self):
        self.booking.status = 'completed'
        self.booking.save()
        res = self.client.post(reverse('cancel-booking', args=['SB-CANCEL01']))
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_cancel_other_users_booking(self):
        other_user = make_user(phone='1112223334')
        other_client = auth_client(other_user)
        res = other_client.post(reverse('cancel-booking', args=['SB-CANCEL01']))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)