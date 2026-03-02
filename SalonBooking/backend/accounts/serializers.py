from rest_framework import serializers
from .models import User, OTP


class SendOTPSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)

    def validate_phone(self, value):
        # Remove spaces and dashes
        value = value.replace(' ', '').replace('-', '')
        if len(value) < 10:
            raise serializers.ValidationError("Invalid phone number")
        return value


class VerifyOTPSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)
    otp = serializers.CharField(max_length=6)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'phone', 'name', 'email', 'is_admin', 'created_at')
        read_only_fields = ('id', 'phone', 'is_admin', 'created_at')