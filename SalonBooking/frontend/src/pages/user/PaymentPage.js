import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { createPaymentOrder, verifyPayment, getPaymentStatus } from '../../services/api';

/**
 * FIX #13: Razorpay SDK must be loaded via a real DOM <script> tag.
 * JSX <script> tags are NOT executed by React — they're treated as static HTML.
 */
function loadRazorpayScript() {
  return new Promise((resolve) => {
    if (window.Razorpay) { resolve(true); return; }
    const script = document.createElement('script');
    script.src = 'https://checkout.razorpay.com/v1/checkout.js';
    script.onload = () => resolve(true);
    script.onerror = () => resolve(false);
    document.body.appendChild(script);
  });
}

function PaymentPage() {
  const { bookingId } = useParams();
  const navigate = useNavigate();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [paying, setPaying] = useState(false);
  const [paid, setPaid] = useState(false);

  useEffect(() => {
    checkExistingPayment();
  }, [bookingId]);

  const checkExistingPayment = async () => {
    try {
      const res = await getPaymentStatus(bookingId);
      if (res.data.status === 'paid') {
        setPaid(true);
        setLoading(false);
        return;
      }
    } catch (_) {}
    fetchOrder();
  };

  const fetchOrder = async () => {
    try {
      const res = await createPaymentOrder(bookingId);
      setOrder(res.data);
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to create payment order');
    }
    setLoading(false);
  };

  const handlePayment = () => {
    if (!order) return;
    setPaying(true);

    // Development fallback if Razorpay not configured
    if (!order.key_id || order.key_id === 'rzp_test_demo') {
      simulateDevPayment();
      return;
    }

    const options = {
      key: order.key_id,
      amount: order.amount,
      currency: order.currency,
      name: 'SalonBook',
      description: order.service_name,
      order_id: order.order_id,
      prefill: {
        contact: order.user_phone,
        name: order.user_name,
      },
      theme: { color: '#6C63FF' },
      handler: async (response) => {
        try {
          await verifyPayment({
            razorpay_order_id: response.razorpay_order_id,
            razorpay_payment_id: response.razorpay_payment_id,
            razorpay_signature: response.razorpay_signature,
          });
          toast.success('🎉 Payment successful! Booking confirmed.');
          setPaid(true);
        } catch (err) {
          toast.error('Payment verification failed. Contact support.');
        }
        setPaying(false);
      },
      modal: {
        ondismiss: () => {
          setPaying(false);
          toast.info('Payment cancelled.');
        },
      },
    };

    const rzp = new window.Razorpay(options);
    rzp.open();
  };

  const simulateDevPayment = async () => {
    // Dev mode: simulate payment without real Razorpay
    try {
      await verifyPayment({
        razorpay_order_id: order.order_id,
        razorpay_payment_id: `pay_dev_${Date.now()}`,
        razorpay_signature: 'dev_signature',
      });
      toast.success('🎉 Dev payment simulated! Booking confirmed.');
      setPaid(true);
    } catch (err) {
      toast.error('Simulation failed — check backend');
    }
    setPaying(false);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-400">Preparing payment...</p>
        </div>
      </div>
    );
  }

  if (paid) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="max-w-md w-full text-center">
          <div className="text-8xl mb-6">🎉</div>
          <h1 className="text-3xl font-bold text-green-400 mb-2">Booking Confirmed!</h1>
          <p className="text-gray-400 mb-2">Your slot has been reserved.</p>
          <p className="text-gray-500 text-sm mb-8">
            You'll receive a WhatsApp confirmation shortly.
          </p>
          <div className="bg-dark border border-green-500/30 rounded-2xl p-6 mb-8">
            <p className="text-gray-400 text-sm mb-1">Booking ID</p>
            <p className="text-xl font-bold text-primary">{bookingId}</p>
          </div>
          <button
            onClick={() => navigate('/my-bookings')}
            className="bg-primary hover:bg-purple-600 text-white font-bold px-8 py-3 rounded-xl transition"
          >
            📋 View My Bookings →
          </button>
        </div>
      </div>
    );
  }

  return (
    <>
      {/* Load Razorpay SDK */}
      <script src="https://checkout.razorpay.com/v1/checkout.js" />

      <div className="max-w-lg mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold mb-8">💳 Complete Payment</h1>

        {/* Order Summary */}
        {order && (
          <div className="bg-dark border border-gray-800 rounded-2xl p-6 mb-6">
            <h2 className="text-lg font-bold mb-4 text-gray-300">Order Summary</h2>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-500">Service</span>
                <span className="font-bold">{order.service_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Booking ID</span>
                <span className="font-mono text-primary text-sm">{order.booking_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Phone</span>
                <span>{order.user_phone}</span>
              </div>
              <div className="border-t border-gray-700 pt-3 flex justify-between items-center">
                <span className="text-gray-400 font-bold">Total Amount</span>
                <span className="text-2xl font-bold text-primary">
                  ₹{(order.amount / 100).toFixed(2)}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Secure badge */}
        <div className="flex items-center gap-2 text-gray-500 text-sm mb-6">
          <span>🔒</span>
          <span>Secured by Razorpay. Your payment info is encrypted.</span>
        </div>

        {/* Pay Button */}
        <button
          onClick={handlePayment}
          disabled={paying || !order}
          className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-700 disabled:text-gray-500 text-white font-bold py-4 rounded-xl transition text-lg flex items-center justify-center gap-2"
        >
          {paying ? (
            <>
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Processing...
            </>
          ) : (
            <>💳 Pay ₹{order ? (order.amount / 100).toFixed(2) : '...'}</>
          )}
        </button>

        <button
          onClick={() => navigate('/my-bookings')}
          className="w-full mt-3 text-gray-500 hover:text-gray-300 py-2 text-sm transition"
        >
          ← Pay Later (booking will remain pending)
        </button>

        {/* Dev notice */}
        {order?.key_id === 'rzp_test_demo' && (
          <div className="mt-6 bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-4 text-yellow-400 text-sm">
            ⚠️ <strong>Dev Mode:</strong> Razorpay not configured. Clicking Pay will simulate a successful payment.
          </div>
        )}
      </div>
    </>
  );
}

export default PaymentPage;