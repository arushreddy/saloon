from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    booking_id = serializers.CharField(source='booking.booking_id', read_only=True)

    class Meta:
        model = Payment
        fields = ('id', 'booking', 'booking_id', 'amount', 'currency', 'status',
                  'razorpay_order_id', 'razorpay_payment_id', 'created_at')
        read_only_fields = ('id', 'razorpay_order_id', 'razorpay_payment_id', 'created_at')


class CreatePaymentSerializer(serializers.Serializer):
    booking_id = serializers.CharField()


class VerifyPaymentSerializer(serializers.Serializer):
    razorpay_order_id = serializers.CharField()
    razorpay_payment_id = serializers.CharField()
    razorpay_signature = serializers.CharField()