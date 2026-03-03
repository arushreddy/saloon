from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Count
from datetime import date, timedelta
from .models import Booking, SlotConfig
from .serializers import (
    BookingSerializer, CreateBookingSerializer,
    SlotConfigSerializer, SlotAvailabilitySerializer
)
from services.models import Service


def get_slot_config(slot_date):
    """
    Returns (config_or_None, is_open, opening, closing, max_per_slot).
    Centralizes default fallback logic in one place.
    """
    try:
        config = SlotConfig.objects.get(date=slot_date)
        return config, config.is_open, config.opening_hour, config.closing_hour, config.max_bookings_per_slot
    except SlotConfig.DoesNotExist:
        return None, True, 9, 21, 5


@api_view(['GET'])
@permission_classes([AllowAny])
def get_available_slots(request):
    """Get available slots for a specific date."""
    slot_date = request.query_params.get('date')
    if not slot_date:
        return Response({'error': 'Date parameter required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        from datetime import datetime
        slot_date = datetime.strptime(slot_date, '%Y-%m-%d').date()
    except ValueError:
        return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)

    if slot_date < date.today():
        return Response({'error': 'Cannot book past dates'}, status=status.HTTP_400_BAD_REQUEST)

    config, is_open, opening, closing, max_per_slot = get_slot_config(slot_date)

    if not is_open:
        return Response({'date': str(slot_date), 'message': 'This date is closed', 'slots': [], 'is_open': False})

    # FIX #2: Count only active bookings (pending + confirmed)
    booked = Booking.objects.filter(
        date=slot_date,
        status__in=['pending', 'confirmed']
    ).values('time_slot').annotate(count=Count('id'))

    booked_map = {item['time_slot']: item['count'] for item in booked}

    slots = []
    for hour in range(opening, closing):
        count = booked_map.get(hour, 0)
        h = hour
        start = f"{h % 12 or 12}:00 {'AM' if h < 12 else 'PM'}"
        eh = h + 1
        end = f"{eh % 12 or 12}:00 {'AM' if eh < 12 else 'PM'}"

        slots.append({
            'hour': hour,
            'time_display': f"{start} — {end}",
            'booked_count': count,
            'max_bookings': max_per_slot,
            'available': count < max_per_slot,
        })

    return Response({
        'date': str(slot_date),
        'is_open': True,
        'opening_hour': opening,
        'closing_hour': closing,
        'slots': slots,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def get_available_dates(request):
    """Get next 30 days with open/closed status."""
    today = date.today()
    dates = []

    # Fetch all SlotConfig rows for the range in ONE query (not 30 queries)
    date_range_end = today + timedelta(days=30)
    configs = SlotConfig.objects.filter(
        date__gte=today,
        date__lte=date_range_end
    )
    config_map = {str(c.date): c for c in configs}

    for i in range(30):
        d = today + timedelta(days=i)
        d_str = str(d)
        config = config_map.get(d_str)

        dates.append({
            'date': d_str,
            'day_name': d.strftime('%A'),
            'is_open': config.is_open if config else True,
            'opening_hour': config.opening_hour if config else 9,
            'closing_hour': config.closing_hour if config else 21,
            'max_bookings_per_slot': config.max_bookings_per_slot if config else 5,
        })

    return Response(dates)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_booking(request):
    """Create a new booking with concurrency safety."""
    serializer = CreateBookingSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    service_id = serializer.validated_data['service_id']
    booking_date = serializer.validated_data['date']
    time_slot = serializer.validated_data['time_slot']
    notes = serializer.validated_data.get('notes', '')

    # Validate service exists
    try:
        service = Service.objects.get(pk=service_id, is_active=True)
    except Service.DoesNotExist:
        return Response({'error': 'Service not found'}, status=status.HTTP_404_NOT_FOUND)

    # Validate date not in past
    if booking_date < date.today():
        return Response({'error': 'Cannot book past dates'}, status=status.HTTP_400_BAD_REQUEST)

    # Get slot config using shared helper
    config, is_open, opening, closing, max_per_slot = get_slot_config(booking_date)

    if not is_open:
        return Response({'error': 'This date is closed'}, status=status.HTTP_400_BAD_REQUEST)

    if time_slot < opening or time_slot >= closing:
        return Response({'error': f'Invalid time slot. Valid range: {opening}:00 — {closing}:00'}, status=status.HTTP_400_BAD_REQUEST)

    # ATOMIC TRANSACTION — prevents race conditions
    with transaction.atomic():
        # Lock rows for this slot to prevent concurrent overbooking
        current_count = Booking.objects.select_for_update().filter(
            date=booking_date,
            time_slot=time_slot,
            status__in=['pending', 'confirmed']  # FIX #2: explicit status filter
        ).count()

        if current_count >= max_per_slot:
            return Response(
                {'error': 'This slot is fully booked. Please choose another time.'},
                status=status.HTTP_409_CONFLICT
            )

        # Check duplicate booking for this user
        exists = Booking.objects.filter(
            user=request.user,
            date=booking_date,
            time_slot=time_slot,
            service=service,
            status__in=['pending', 'confirmed']
        ).exists()

        if exists:
            return Response(
                {'error': 'You already have a booking for this slot and service.'},
                status=status.HTTP_409_CONFLICT
            )

        booking = Booking.objects.create(
            user=request.user,
            service=service,
            date=booking_date,
            time_slot=time_slot,
            notes=notes,
            status='pending'
        )

    return Response({
        'message': 'Booking created! Complete payment to confirm.',
        'booking': BookingSerializer(booking).data
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_bookings(request):
    """Get current user's bookings."""
    filter_status = request.query_params.get('status')
    bookings = Booking.objects.filter(user=request.user).select_related('service')

    if filter_status:
        bookings = bookings.filter(status=filter_status)

    serializer = BookingSerializer(bookings, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_booking(request, booking_id):
    """Cancel a booking."""
    try:
        booking = Booking.objects.get(booking_id=booking_id, user=request.user)
    except Booking.DoesNotExist:
        return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)

    if booking.status in ['cancelled', 'completed']:
        return Response({'error': f'Cannot cancel a {booking.status} booking.'}, status=status.HTTP_400_BAD_REQUEST)

    booking.status = 'cancelled'
    booking.save()

    # Send cancellation WhatsApp
    try:
        from notifications.utils import send_cancellation_message
        send_cancellation_message(booking)
    except Exception as e:
        print(f"[WhatsApp] Cancellation notification failed: {e}")

    return Response({'message': 'Booking cancelled', 'booking': BookingSerializer(booking).data})


# ── ADMIN ENDPOINTS ─────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_all_bookings(request):
    """Admin: View all bookings with filters."""
    if not request.user.is_admin:
        return Response({'error': 'Admin only'}, status=status.HTTP_403_FORBIDDEN)

    bookings = Booking.objects.all().select_related('user', 'service')

    filter_date = request.query_params.get('date')
    filter_status = request.query_params.get('status')
    filter_service = request.query_params.get('service_id')

    if filter_date:
        bookings = bookings.filter(date=filter_date)
    if filter_status:
        bookings = bookings.filter(status=filter_status)
    if filter_service:
        bookings = bookings.filter(service_id=filter_service)

    serializer = BookingSerializer(bookings, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_update_slot(request):
    """Admin: Open/close dates and configure slots."""
    if not request.user.is_admin:
        return Response({'error': 'Admin only'}, status=status.HTTP_403_FORBIDDEN)

    serializer = SlotConfigSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    slot_date = serializer.validated_data['date']

    # Validate hours
    opening = serializer.validated_data.get('opening_hour', 9)
    closing = serializer.validated_data.get('closing_hour', 21)
    if opening >= closing:
        return Response({'error': 'Opening hour must be before closing hour'}, status=status.HTTP_400_BAD_REQUEST)

    config, created = SlotConfig.objects.update_or_create(
        date=slot_date,
        defaults=serializer.validated_data
    )

    return Response({
        'message': 'Slot updated',
        'slot': SlotConfigSerializer(config).data
    })


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def admin_update_booking_status(request, booking_id):
    """Admin: Update booking status."""
    if not request.user.is_admin:
        return Response({'error': 'Admin only'}, status=status.HTTP_403_FORBIDDEN)

    try:
        booking = Booking.objects.get(booking_id=booking_id)
    except Booking.DoesNotExist:
        return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)

    valid_statuses = ['pending', 'confirmed', 'completed', 'cancelled', 'no_show']
    new_status = request.data.get('status')
    if new_status not in valid_statuses:
        return Response({'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}, status=status.HTTP_400_BAD_REQUEST)

    old_status = booking.status
    booking.status = new_status
    booking.save()

    # Send WhatsApp notification on confirm
    if old_status != 'confirmed' and new_status == 'confirmed':
        try:
            from notifications.utils import send_booking_confirmation
            send_booking_confirmation(booking)
        except Exception as e:
            print(f"[WhatsApp] Notification failed: {e}")

    return Response({'message': 'Status updated', 'booking': BookingSerializer(booking).data})