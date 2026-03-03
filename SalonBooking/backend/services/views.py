from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .models import Service
from .serializers import ServiceSerializer, ServiceListSerializer


@api_view(['GET'])
@permission_classes([AllowAny])
def list_services(request):
    """
    Public: List all active services.
    FIX #5: Admin users can also see inactive services by passing ?all=true
    """
    # Check if requester is admin and wants all services
    show_all = (
        request.query_params.get('all') == 'true'
        and request.user.is_authenticated
        and request.user.is_admin
    )

    services = Service.objects.all() if show_all else Service.objects.filter(is_active=True)

    category = request.query_params.get('category')
    if category:
        services = services.filter(category__iexact=category)

    serializer = ServiceListSerializer(services, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def service_detail(request, pk):
    """Public: Get single service details."""
    try:
        service = Service.objects.get(pk=pk, is_active=True)
    except Service.DoesNotExist:
        return Response({'error': 'Service not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = ServiceSerializer(service)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def service_categories(request):
    """Public: Get all unique non-empty categories."""
    categories = (
        Service.objects
        .filter(is_active=True)
        .exclude(category='')
        .values_list('category', flat=True)
        .distinct()
        .order_by('category')
    )
    return Response(list(categories))


# ── ADMIN ENDPOINTS ─────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_service(request):
    """Admin: Create new service."""
    if not request.user.is_admin:
        return Response({'error': 'Admin only'}, status=status.HTTP_403_FORBIDDEN)

    serializer = ServiceSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    service = serializer.save()
    return Response(ServiceSerializer(service).data, status=status.HTTP_201_CREATED)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_service(request, pk):
    """Admin: Update service (partial update supported)."""
    if not request.user.is_admin:
        return Response({'error': 'Admin only'}, status=status.HTTP_403_FORBIDDEN)

    try:
        service = Service.objects.get(pk=pk)  # Admin can edit even inactive
    except Service.DoesNotExist:
        return Response({'error': 'Service not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = ServiceSerializer(service, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_service(request, pk):
    """Admin: Soft-delete (deactivate) service."""
    if not request.user.is_admin:
        return Response({'error': 'Admin only'}, status=status.HTTP_403_FORBIDDEN)

    try:
        service = Service.objects.get(pk=pk)
    except Service.DoesNotExist:
        return Response({'error': 'Service not found'}, status=status.HTTP_404_NOT_FOUND)

    if not service.is_active:
        return Response({'error': 'Service is already deactivated'}, status=status.HTTP_400_BAD_REQUEST)

    service.is_active = False
    service.save()
    return Response({'message': f'Service "{service.name}" deactivated successfully'})