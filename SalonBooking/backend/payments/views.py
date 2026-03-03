from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Payment
from .serializers import PaymentSerializer, CreatePaymentSerializer, VerifyPaymentSerializer
from bookings.models import Booking


def get_razorpay_client():
    """
    FIX #4: Lazy Razorpay client initialization.
    Old code initialized at module load — if env vars added later, no effect.
    Now creates client on demand so it always picks up current settings.
    """
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        return None
    try:
        import razorpay
        return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    except ImportError:
        print("[Razorpay] razorpay package not installed")
        return None


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_order(request):
    """Create Razorpay order for a booking."""
    serializer = CreatePaymentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    booking_id = serializer.validated_data['booking_id']

    try:
        booking = Booking.objects.get(
            booking_id=booking_id,
            user=request.user,
            status='pending'
        )
    except Booking.DoesNotExist:
        return Response({'error': 'Booking not found or already paid'}, status=status.HTTP_404_NOT_FOUND)

    # Prevent duplicate paid orders
    if hasattr(booking, 'payment') and booking.payment.status == 'paid':
        return Response({'error': 'This booking is already paid'}, status=status.HTTP_400_BAD_REQUEST)

    amount = int(booking.service.price * 100)  # Razorpay uses paise

    client = get_razorpay_client()

    if client:
        try:
            razorpay_order = client.order.create({
                'amount': amount,
                'currency': 'INR',
                'payment_capture': 1,
                'notes': {
                    'booking_id': booking.booking_id,
                    'service': booking.service.name,
                    'user_phone': request.user.phone,
                }
            })
            razorpay_order_id = razorpay_order['id']
        except Exception as e:
            return Response(
                {'error': f'Payment gateway error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    else:
        # Development mode — fake order ID
        import uuid
        razorpay_order_id = f"order_dev_{uuid.uuid4().hex[:12]}"

    payment, _ = Payment.objects.update_or_create(
        booking=booking,
        defaults={
            'user': request.user,
            'amount': booking.service.price,
            'razorpay_order_id': razorpay_order_id,
            'status': 'created',
        }
    )

    return Response({
        'order_id': razorpay_order_id,
        'amount': amount,
        'currency': 'INR',
        'booking_id': booking.booking_id,
        'key_id': settings.RAZORPAY_KEY_ID or 'rzp_test_demo',
        'user_phone': request.user.phone,
        'user_name': request.user.name,
        'service_name': booking.service.name,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_payment(request):
    """Verify Razorpay payment signature and confirm booking."""
    serializer = VerifyPaymentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    razorpay_order_id = serializer.validated_data['razorpay_order_id']
    razorpay_payment_id = serializer.validated_data['razorpay_payment_id']
    razorpay_signature = serializer.validated_data['razorpay_signature']

    try:
        payment = Payment.objects.select_related('booking__service', 'booking__user').get(
            razorpay_order_id=razorpay_order_id
        )
    except Payment.DoesNotExist:
        return Response({'error': 'Payment record not found'}, status=status.HTTP_404_NOT_FOUND)

    # Prevent double-processing
    if payment.status == 'paid':
        return Response({'error': 'Payment already verified'}, status=status.HTTP_400_BAD_REQUEST)

    client = get_razorpay_client()

    # FIX #3: Only skip signature check in dev mode (when no real client)
    # In production with real keys, ALWAYS verify signature
    if client:
        try:
            import razorpay
            client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature,
            })
        except razorpay.errors.SignatureVerificationError:
            payment.status = 'failed'
            payment.save()
            return Response(
                {'error': 'Payment verification failed. Invalid signature.'},
                status=status.HTTP_400_BAD_REQUEST
            )
    else:
        # Dev mode: only allow dev payment IDs to simulate payment
        if not razorpay_order_id.startswith('order_dev_'):
            return Response(
                {'error': 'Cannot verify real Razorpay payments without API keys configured.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    # Payment successful
    payment.razorpay_payment_id = razorpay_payment_id
    payment.razorpay_signature = razorpay_signature
    payment.status = 'paid'
    payment.save()

    booking = payment.booking
    booking.status = 'confirmed'
    booking.save()

    # Send WhatsApp confirmation
    try:
        from notifications.utils import send_booking_confirmation
        send_booking_confirmation(booking)
    except Exception as e:
        print(f"[WhatsApp] Notification failed: {e}")

    return Response({
        'message': 'Payment successful! Booking confirmed.',
        'booking': {
            'booking_id': booking.booking_id,
            'service': booking.service.name,
            'date': str(booking.date),
            'time_slot': f"{booking.time_slot}:00",
            'status': booking.status,
        },
        'payment': {
            'amount': str(payment.amount),
            'transaction_id': razorpay_payment_id,
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_status(request, booking_id):
    """Check payment status for a booking."""
    try:
        booking = Booking.objects.get(booking_id=booking_id, user=request.user)
        payment = Payment.objects.get(booking=booking)
    except Booking.DoesNotExist:
        return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)
    except Payment.DoesNotExist:
        return Response({'error': 'No payment record for this booking'}, status=status.HTTP_404_NOT_FOUND)

    return Response(PaymentSerializer(payment).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_all_payments(request):
    """Admin: View all payments."""
    if not request.user.is_admin:
        return Response({'error': 'Admin only'}, status=status.HTTP_403_FORBIDDEN)

    payments = Payment.objects.all().select_related('booking', 'user')

    filter_status = request.query_params.get('status')
    if filter_status:
        payments = payments.filter(status=filter_status)

    serializer = PaymentSerializer(payments, many=True)
    return Response(serializer.data)