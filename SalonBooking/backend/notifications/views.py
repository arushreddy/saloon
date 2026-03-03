from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .utils import send_whatsapp_message
from .email_utils import send_email


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_whatsapp(request):
    """Admin: Test WhatsApp integration."""
    if not request.user.is_admin:
        return Response({'error': 'Admin only'}, status=403)

    phone = request.data.get('phone', request.user.phone)
    message = request.data.get('message', '🧪 Test message from Salon Booking App!')

    success = send_whatsapp_message(phone, message)
    return Response({'sent': success, 'phone': phone})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_email(request):
    """Admin: Test email integration."""
    if not request.user.is_admin:
        return Response({'error': 'Admin only'}, status=403)

    to_email = request.data.get('email', request.user.email)

    if not to_email:
        return Response({'error': 'No email address provided'}, status=400)

    html = f"""
    <div style="background:#0f0f1a;padding:40px;font-family:Arial;color:#fff;text-align:center;">
        <div style="font-size:48px;">💈</div>
        <h1 style="color:#8B5CF6;">SalonBook</h1>
        <p style="color:#9CA3AF;">Test email working! ✅</p>
    </div>
    """

    success = send_email(
        to_email=to_email,
        subject='🧪 SalonBook — Test Email',
        html_content=html,
    )

    return Response({
        'sent': success,
        'to': to_email,
        'message': 'Email sent!' if success else 'Failed — check .env settings'
    })