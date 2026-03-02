import React from 'react';
import { useParams } from 'react-router-dom';

function PaymentPage() {
  const { bookingId } = useParams();
  return (
    <div className="max-w-lg mx-auto px-4 py-8 text-center">
      <h1 className="text-2xl font-bold mb-4">💳 Payment</h1>
      <p className="text-gray-400 mb-4">Booking: {bookingId}</p>
      <p className="text-green-400">Razorpay integration coming next!</p>
    </div>
  );
}

export default PaymentPage;