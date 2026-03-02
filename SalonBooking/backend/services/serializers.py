from rest_framework import serializers
from .models import Service


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'


class ServiceListSerializer(serializers.ModelSerializer):
    """Lighter serializer for listing services."""
    class Meta:
        model = Service
        fields = ('id', 'name', 'description', 'price', 'duration_minutes',
                  'image', 'category', 'is_active')