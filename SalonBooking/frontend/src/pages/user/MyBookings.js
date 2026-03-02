import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import { getMyBookings, cancelBooking } from '../../services/api';

function MyBookings() {
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { fetchBookings(); }, []);

  const fetchBookings = async () => {
    try {
      const res = await getMyBookings();
      setBookings(res.data);
    } catch (err) { toast.error('Failed to load bookings'); }
    setLoading(false);
  };

  const handleCancel = async (bookingId) => {
    if (!window.confirm('Cancel this booking?')) return;
    try {
      await cancelBooking(bookingId);
      toast.success('Booking cancelled');
      fetchBookings();
    } catch (err) { toast.error('Failed to cancel'); }
  };

  const statusColors = {
    pending: 'text-yellow-400 bg-yellow-400/10',
    confirmed: 'text-green-400 bg-green-400/10',
    completed: 'text-blue-400 bg-blue-400/10',
    cancelled: 'text-red-400 bg-red-400/10',
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">📋 My Bookings</h1>
      {loading ? <p className="text-gray-500">Loading...</p> :
       bookings.length === 0 ? <p className="text-gray-500">No bookings yet.</p> :
        <div className="space-y-4">
          {bookings.map((b) => (
            <div key={b.id} className="bg-dark border border-gray-800 rounded-xl p-5">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-bold text-lg">{b.service_detail?.name}</h3>
                  <p className="text-gray-400 text-sm mt-1">🎫 {b.booking_id}</p>
                  <p className="text-gray-400 text-sm">📅 {b.date} • 🕐 {b.time_display}</p>
                </div>
                <div className="text-right">
                  <span className={`px-3 py-1 rounded-full text-xs font-bold ${statusColors[b.status] || ''}`}>
                    {b.status?.toUpperCase()}
                  </span>
                  <p className="text-primary font-bold mt-2">₹{b.service_detail?.price}</p>
                </div>
              </div>
              {['pending', 'confirmed'].includes(b.status) && (
                <button onClick={() => handleCancel(b.booking_id)}
                  className="mt-3 text-red-400 text-sm hover:text-red-300 transition">
                  ❌ Cancel Booking
                </button>
              )}
            </div>
          ))}
        </div>
      }
    </div>
  );
}

export default MyBookings;