from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .utils import send_whatsapp_message


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_whatsapp(request):
    """Admin: Test WhatsApp integration."""
    if not request.user.is_admin:
        return Response({'error': 'Admin only'}, status=403)

    phone = request.data.get('phone', request.user.phone)
    message = request.data.get('message', '🧪 Test message from Salon Booking App!')

    success = send_whatsapp_message(phone, message)
    return Response({
        'sent': success,
        'phone': phone,
    })