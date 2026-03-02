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

    # Check if date is in the past
    if slot_date < date.today():
        return Response({'error': 'Cannot book past dates'}, status=status.HTTP_400_BAD_REQUEST)

    # Get slot config for this date (or use defaults)
    try:
        config = SlotConfig.objects.get(date=slot_date)
        if not config.is_open:
            return Response({'message': 'This date is closed', 'slots': []})
        opening = config.opening_hour
        closing = config.closing_hour
        max_per_slot = config.max_bookings_per_slot
    except SlotConfig.DoesNotExist:
        # Default: open 9AM-9PM, 5 per slot
        opening = 9
        closing = 21
        max_per_slot = 5

    # Count bookings per slot
    booked = Booking.objects.filter(
        date=slot_date,
        status__in=['pending', 'confirmed']
    ).values('time_slot').annotate(count=Count('id'))

    booked_map = {item['time_slot']: item['count'] for item in booked}

    # Build slots
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

    for i in range(30):
        d = today + timedelta(days=i)
        try:
            config = SlotConfig.objects.get(date=d)
            is_open = config.is_open
        except SlotConfig.DoesNotExist:
            is_open = True  # Default: open

        dates.append({
            'date': str(d),
            'day_name': d.strftime('%A'),
            'is_open': is_open,
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

    # Get slot config
    try:
        config = SlotConfig.objects.get(date=booking_date)
        if not config.is_open:
            return Response({'error': 'This date is closed'}, status=status.HTTP_400_BAD_REQUEST)
        max_per_slot = config.max_bookings_per_slot
        if time_slot < config.opening_hour or time_slot >= config.closing_hour:
            return Response({'error': 'Invalid time slot for this date'}, status=status.HTTP_400_BAD_REQUEST)
    except SlotConfig.DoesNotExist:
        max_per_slot = 5
        if time_slot < 9 or time_slot >= 21:
            return Response({'error': 'Invalid time slot'}, status=status.HTTP_400_BAD_REQUEST)

    # ATOMIC TRANSACTION — prevents race conditions
    with transaction.atomic():
        # Lock and count current bookings for this slot
        current_count = Booking.objects.select_for_update().filter(
            date=booking_date,
            time_slot=time_slot,
            status__in=['pending', 'confirmed']
        ).count()

        if current_count >= max_per_slot:
            return Response(
                {'error': 'This slot is fully booked'},
                status=status.HTTP_409_CONFLICT
            )

        # Check duplicate booking
        exists = Booking.objects.filter(
            user=request.user,
            date=booking_date,
            time_slot=time_slot,
            service=service,
            status__in=['pending', 'confirmed']
        ).exists()

        if exists:
            return Response(
                {'error': 'You already have a booking for this slot'},
                status=status.HTTP_409_CONFLICT
            )

        # Create booking
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
    bookings = Booking.objects.filter(user=request.user)

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
        return Response({'error': 'Cannot cancel this booking'}, status=status.HTTP_400_BAD_REQUEST)

    booking.status = 'cancelled'
    booking.save()
    return Response({'message': 'Booking cancelled', 'booking': BookingSerializer(booking).data})


# ── ADMIN ENDPOINTS ─────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_all_bookings(request):
    """Admin: View all bookings with filters."""
    if not request.user.is_admin:
        return Response({'error': 'Admin only'}, status=status.HTTP_403_FORBIDDEN)

    bookings = Booking.objects.all()

    # Filters
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

    new_status = request.data.get('status')
    if new_status not in ['pending', 'confirmed', 'completed', 'cancelled', 'no_show']:
        return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)

    booking.status = new_status
    booking.save()
    return Response({'message': 'Status updated', 'booking': BookingSerializer(booking).data})