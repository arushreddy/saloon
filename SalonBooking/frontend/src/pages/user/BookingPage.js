import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { getServiceDetail, getAvailableDates, getAvailableSlots, createBooking } from '../../services/api';

function BookingPage() {
  const { serviceId } = useParams();
  const navigate = useNavigate();
  const [service, setService] = useState(null);
  const [dates, setDates] = useState([]);
  const [slots, setSlots] = useState([]);
  const [selectedDate, setSelectedDate] = useState('');
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [loading, setLoading] = useState(true);
  const [booking, setBooking] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (selectedDate) fetchSlots(selectedDate);
  }, [selectedDate]);

  const fetchData = async () => {
    try {
      const [svcRes, datesRes] = await Promise.all([
        getServiceDetail(serviceId),
        getAvailableDates()
      ]);
      setService(svcRes.data);
      setDates(datesRes.data.filter(d => d.is_open));
    } catch (err) {
      toast.error('Failed to load data');
    }
    setLoading(false);
  };

  const fetchSlots = async (date) => {
    try {
      const res = await getAvailableSlots(date);
      setSlots(res.data.slots || []);
    } catch (err) {
      toast.error('Failed to load slots');
    }
  };

  const handleBook = async () => {
    if (!selectedDate || selectedSlot === null) {
      toast.error('Select a date and time slot');
      return;
    }
    setBooking(true);
    try {
      const res = await createBooking({
        service_id: parseInt(serviceId),
        date: selectedDate,
        time_slot: selectedSlot,
      });
      toast.success('Booking created! Proceed to payment.');
      navigate(`/payment/${res.data.booking.booking_id}`);
    } catch (err) {
      toast.error(err.response?.data?.error || 'Booking failed');
    }
    setBooking(false);
  };

  if (loading) return <div className="text-center py-20 text-gray-500">Loading...</div>;
  if (!service) return <div className="text-center py-20 text-red-400">Service not found</div>;

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Service Info */}
      <div className="bg-dark border border-gray-800 rounded-2xl p-6 mb-8">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 bg-primary/10 rounded-xl flex items-center justify-center text-3xl">💇</div>
          <div>
            <h1 className="text-2xl font-bold">{service.name}</h1>
            <div className="flex items-center gap-4 text-gray-400 mt-1">
              <span className="text-primary font-bold text-xl">₹{service.price}</span>
              <span>⏱ {service.duration_minutes} min</span>
            </div>
          </div>
        </div>
      </div>

      {/* Step 1: Select Date */}
      <div className="mb-8">
        <h2 className="text-lg font-bold mb-4">📅 Step 1: Select Date</h2>
        <div className="flex gap-3 overflow-x-auto pb-2">
          {dates.map((d) => {
            const dateObj = new Date(d.date + 'T00:00:00');
            const day = dateObj.getDate();
            const month = dateObj.toLocaleString('default', { month: 'short' });
            const dayName = d.day_name.slice(0, 3);
            const isSelected = selectedDate === d.date;

            return (
              <button
                key={d.date}
                onClick={() => { setSelectedDate(d.date); setSelectedSlot(null); }}
                className={`flex-shrink-0 w-20 py-3 rounded-xl text-center transition border ${
                  isSelected
                    ? 'bg-primary border-primary text-white'
                    : 'bg-dark border-gray-700 hover:border-primary text-gray-300'
                }`}
              >
                <div className="text-xs font-medium opacity-70">{dayName}</div>
                <div className="text-xl font-bold">{day}</div>
                <div className="text-xs opacity-70">{month}</div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Step 2: Select Slot */}
      {selectedDate && (
        <div className="mb-8">
          <h2 className="text-lg font-bold mb-4">🕐 Step 2: Select Time Slot</h2>
          {slots.length === 0 ? (
            <p className="text-gray-500">No slots available for this date.</p>
          ) : (
            <div className="grid grid-cols-3 md:grid-cols-4 gap-3">
              {slots.map((slot) => (
                <button
                  key={slot.hour}
                  onClick={() => slot.available && setSelectedSlot(slot.hour)}
                  disabled={!slot.available}
                  className={`py-3 px-2 rounded-xl text-center transition border text-sm ${
                    !slot.available
                      ? 'bg-red-900/20 border-red-900/30 text-red-400 cursor-not-allowed opacity-50'
                      : selectedSlot === slot.hour
                      ? 'bg-primary border-primary text-white'
                      : 'bg-dark border-gray-700 hover:border-primary text-gray-300'
                  }`}
                >
                  <div className="font-bold">{slot.time_display}</div>
                  <div className="text-xs mt-1 opacity-70">
                    {slot.available
                      ? `${slot.max_bookings - slot.booked_count} left`
                      : 'Full'}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Booking Summary & Confirm */}
      {selectedDate && selectedSlot !== null && (
        <div className="bg-dark border border-primary/30 rounded-2xl p-6">
          <h2 className="text-lg font-bold mb-4">✅ Booking Summary</h2>
          <div className="grid grid-cols-2 gap-4 mb-6 text-sm">
            <div><span className="text-gray-500">Service:</span> <span className="font-bold">{service.name}</span></div>
            <div><span className="text-gray-500">Price:</span> <span className="font-bold text-primary">₹{service.price}</span></div>
            <div><span className="text-gray-500">Date:</span> <span className="font-bold">{selectedDate}</span></div>
            <div><span className="text-gray-500">Time:</span> <span className="font-bold">{slots.find(s => s.hour === selectedSlot)?.time_display}</span></div>
          </div>

          <button
            onClick={handleBook}
            disabled={booking}
            className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-700 text-white font-bold py-4 rounded-xl transition text-lg"
          >
            {booking ? '⏳ Creating Booking...' : '💳 Proceed to Payment →'}
          </button>
        </div>
      )}
    </div>
  );
}

export default BookingPage;