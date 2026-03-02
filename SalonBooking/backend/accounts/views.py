import random
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, OTP
from .serializers import SendOTPSerializer, VerifyOTPSerializer, UserSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def send_otp(request):
    """Send OTP to phone number."""
    serializer = SendOTPSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    phone = serializer.validated_data['phone']

    # Rate limit: max 5 OTPs per phone per hour
    from django.utils import timezone
    from datetime import timedelta
    recent = OTP.objects.filter(
        phone=phone,
        created_at__gte=timezone.now() - timedelta(hours=1)
    ).count()
    if recent >= 5:
        return Response(
            {'error': 'Too many OTP requests. Try again later.'},
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )

    # Generate 6-digit OTP
    otp_code = str(random.randint(100000, 999999))

    # Save OTP
    OTP.objects.create(phone=phone, otp=otp_code)

    # TODO: Send OTP via MSG91 or Firebase in production
    # For development, we return OTP in response
    print(f"[OTP] {phone} → {otp_code}")

    return Response({
        'message': 'OTP sent successfully',
        'phone': phone,
        'otp_debug': otp_code  # REMOVE THIS IN PRODUCTION
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    """Verify OTP and return JWT tokens."""
    serializer = VerifyOTPSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    phone = serializer.validated_data['phone']
    otp_code = serializer.validated_data['otp']

    # Find latest OTP for this phone
    try:
        otp_obj = OTP.objects.filter(
            phone=phone,
            is_verified=False
        ).latest('created_at')
    except OTP.DoesNotExist:
        return Response(
            {'error': 'No OTP found. Request a new one.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check expiry
    if otp_obj.is_expired():
        return Response(
            {'error': 'OTP expired. Request a new one.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check attempts
    if otp_obj.attempts >= 3:
        return Response(
            {'error': 'Too many attempts. Request a new OTP.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Verify
    otp_obj.attempts += 1
    otp_obj.save()

    if otp_obj.otp != otp_code:
        return Response(
            {'error': f'Invalid OTP. {3 - otp_obj.attempts} attempts remaining.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Mark verified
    otp_obj.is_verified = True
    otp_obj.save()

    # Get or create user
    user, created = User.objects.get_or_create(phone=phone)

    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)

    return Response({
        'message': 'Login successful',
        'is_new_user': created,
        'tokens': {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        },
        'user': UserSerializer(user).data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profile(request):
    """Get current user profile."""
    return Response(UserSerializer(request.user).data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """Update user name and email."""
    serializer = UserSerializer(request.user, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)