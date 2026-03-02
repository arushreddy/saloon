"""
Bookings — Slots, Reservations, and Scheduling
"""

from django.db import models
from django.conf import settings


class SlotConfig(models.Model):
    """Admin controls which dates and hours are open."""

    date = models.DateField(unique=True)
    is_open = models.BooleanField(default=True)
    opening_hour = models.IntegerField(default=9)    # 9 AM
    closing_hour = models.IntegerField(default=21)   # 9 PM
    max_bookings_per_slot = models.IntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date']

    def __str__(self):
        status = "OPEN" if self.is_open else "CLOSED"
        return f"{self.date} [{status}] {self.opening_hour}:00 — {self.closing_hour}:00"


class Booking(models.Model):
    """Each customer booking."""

    STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]

    booking_id = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    service = models.ForeignKey(
        'services.Service',
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    date = models.DateField()
    time_slot = models.IntegerField(help_text="Hour in 24h format (e.g. 9 = 9AM, 14 = 2PM)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', 'time_slot']
        # Prevent same user booking same slot twice
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'date', 'time_slot', 'service'],
                name='unique_user_booking_per_slot'
            )
        ]

    def save(self, *args, **kwargs):
        if not self.booking_id:
            import uuid
            self.booking_id = f"SB-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.booking_id} | {self.user.phone} | {self.service.name} | {self.date} {self.time_slot}:00"

    @staticmethod
    def get_slot_count(date, time_slot):
        """How many bookings exist for this slot."""
        return Booking.objects.filter(
            date=date,
            time_slot=time_slot,
            status__in=['pending', 'confirmed']
        ).count()

    @staticmethod
    def is_slot_available(date, time_slot, max_per_slot=5):
        """Check if slot still has room."""
        return Booking.get_slot_count(date, time_slot) < max_per_slot