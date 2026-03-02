from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .models import Service
from .serializers import ServiceSerializer, ServiceListSerializer


@api_view(['GET'])
@permission_classes([AllowAny])
def list_services(request):
    """Public: List all active services."""
    services = Service.objects.filter(is_active=True)

    # Filter by category if provided
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
    """Public: Get all unique categories."""
    categories = Service.objects.filter(
        is_active=True
    ).values_list('category', flat=True).distinct()
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
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_service(request, pk):
    """Admin: Update service."""
    if not request.user.is_admin:
        return Response({'error': 'Admin only'}, status=status.HTTP_403_FORBIDDEN)

    try:
        service = Service.objects.get(pk=pk)
    except Service.DoesNotExist:
        return Response({'error': 'Service not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = ServiceSerializer(service, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_service(request, pk):
    """Admin: Delete (deactivate) service."""
    if not request.user.is_admin:
        return Response({'error': 'Admin only'}, status=status.HTTP_403_FORBIDDEN)

    try:
        service = Service.objects.get(pk=pk)
    except Service.DoesNotExist:
        return Response({'error': 'Service not found'}, status=status.HTTP_404_NOT_FOUND)

    service.is_active = False
    service.save()
    return Response({'message': 'Service deactivated'})