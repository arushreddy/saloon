from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Sum
from datetime import date, timedelta
from bookings.models import Booking
from payments.models import Payment
from accounts.models import User
from services.models import Service


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_analytics(request):
    """Admin: Get dashboard analytics."""
    if not request.user.is_admin:
        return Response({'error': 'Admin only'}, status=403)

    today = date.today()
    month_start = today.replace(day=1)

    # Counts
    total_users = User.objects.count()
    total_bookings = Booking.objects.count()
    total_services = Service.objects.filter(is_active=True).count()

    # Today's bookings
    today_bookings = Booking.objects.filter(date=today, status__in=['confirmed', 'pending']).count()

    # This month revenue
    month_revenue = Payment.objects.filter(
        status='paid',
        created_at__date__gte=month_start
    ).aggregate(total=Sum('amount'))['total'] or 0

    # Total revenue
    total_revenue = Payment.objects.filter(
        status='paid'
    ).aggregate(total=Sum('amount'))['total'] or 0

    # Booking status breakdown
    status_breakdown = Booking.objects.values('status').annotate(count=Count('id'))

    # Popular services
    popular = Booking.objects.filter(
        status__in=['confirmed', 'completed']
    ).values('service__name').annotate(
        count=Count('id')
    ).order_by('-count')[:5]

    # This week bookings (day by day)
    week_start = today - timedelta(days=today.weekday())
    weekly = []
    for i in range(7):
        d = week_start + timedelta(days=i)
        count = Booking.objects.filter(date=d, status__in=['confirmed', 'completed']).count()
        weekly.append({'date': str(d), 'day': d.strftime('%A'), 'bookings': count})

    return Response({
        'total_users': total_users,
        'total_bookings': total_bookings,
        'total_services': total_services,
        'today_bookings': today_bookings,
        'month_revenue': str(month_revenue),
        'total_revenue': str(total_revenue),
        'status_breakdown': list(status_breakdown),
        'popular_services': list(popular),
        'weekly_bookings': weekly,
    })