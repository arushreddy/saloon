from rest_framework import serializers
from .models import Booking, SlotConfig
from services.serializers import ServiceListSerializer


class SlotConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = SlotConfig
        fields = '__all__'


class BookingSerializer(serializers.ModelSerializer):
    service_detail = ServiceListSerializer(source='service', read_only=True)
    # FIX #6: Don't expose user FK (integer ID) — only expose safe display fields
    user_phone = serializers.CharField(source='user.phone', read_only=True)
    user_name = serializers.CharField(source='user.name', read_only=True)
    time_display = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = (
            'id', 'booking_id',
            # Removed raw 'user' FK — replaced with safe read-only display fields
            'user_phone', 'user_name',
            'service', 'service_detail',
            'date', 'time_slot', 'time_display',
            'status', 'notes', 'created_at'
        )
        read_only_fields = ('id', 'booking_id', 'created_at')

    def get_time_display(self, obj):
        h = obj.time_slot
        start = f"{h % 12 or 12}:00 {'AM' if h < 12 else 'PM'}"
        eh = h + 1
        end = f"{eh % 12 or 12}:00 {'AM' if eh < 12 else 'PM'}"
        return f"{start} — {end}"


class CreateBookingSerializer(serializers.Serializer):
    service_id = serializers.IntegerField()
    date = serializers.DateField()
    time_slot = serializers.IntegerField(min_value=0, max_value=23)
    notes = serializers.CharField(required=False, default='', allow_blank=True)

    def validate_date(self, value):
        from datetime import date
        if value < date.today():
            raise serializers.ValidationError("Cannot book a past date.")
        return value


class SlotAvailabilitySerializer(serializers.Serializer):
    hour = serializers.IntegerField()
    time_display = serializers.CharField()
    booked_count = serializers.IntegerField()
    max_bookings = serializers.IntegerField()
    available = serializers.BooleanField()