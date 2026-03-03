import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import { adminGetBookings, adminUpdateBookingStatus } from '../../services/api';

const STATUS_STYLES = {
  pending: 'text-yellow-400 bg-yellow-400/10 border-yellow-400/30',
  confirmed: 'text-green-400 bg-green-400/10 border-green-400/30',
  completed: 'text-blue-400 bg-blue-400/10 border-blue-400/30',
  cancelled: 'text-red-400 bg-red-400/10 border-red-400/30',
  no_show: 'text-gray-400 bg-gray-400/10 border-gray-400/30',
};

const ALL_STATUSES = ['pending', 'confirmed', 'completed', 'cancelled', 'no_show'];

function StatusBadge({ status }) {
  return (
    <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${STATUS_STYLES[status] || ''}`}>
      {status?.replace('_', ' ').toUpperCase()}
    </span>
  );
}

function AdminBookings() {
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ date: '', status: '', service_id: '' });
  const [updating, setUpdating] = useState(null);

  useEffect(() => { fetchBookings(); }, []);

  const fetchBookings = async () => {
    setLoading(true);
    try {
      const params = {};
      if (filters.date) params.date = filters.date;
      if (filters.status) params.status = filters.status;
      if (filters.service_id) params.service_id = filters.service_id;
      const res = await adminGetBookings(params);
      setBookings(res.data);
    } catch (err) {
      toast.error('Failed to load bookings');
    }
    setLoading(false);
  };

  const handleStatusChange = async (bookingId, newStatus) => {
    setUpdating(bookingId);
    try {
      await adminUpdateBookingStatus(bookingId, newStatus);
      toast.success('Status updated');
      setBookings(prev =>
        prev.map(b => b.booking_id === bookingId ? { ...b, status: newStatus } : b)
      );
    } catch (err) {
      toast.error('Failed to update status');
    }
    setUpdating(null);
  };

  const applyFilters = (e) => {
    e.preventDefault();
    fetchBookings();
  };

  const clearFilters = () => {
    setFilters({ date: '', status: '', service_id: '' });
    setTimeout(fetchBookings, 0);
  };

  const statusCounts = ALL_STATUSES.reduce((acc, s) => {
    acc[s] = bookings.filter(b => b.status === s).length;
    return acc;
  }, {});

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-2">📋 All Bookings</h1>
      <p className="text-gray-500 text-sm mb-6">{bookings.length} bookings found</p>

      {/* Status Summary Chips */}
      <div className="flex flex-wrap gap-2 mb-6">
        {ALL_STATUSES.map(s => (
          <button
            key={s}
            onClick={() => {
              setFilters(prev => ({ ...prev, status: prev.status === s ? '' : s }));
              setTimeout(fetchBookings, 50);
            }}
            className={`px-3 py-1.5 rounded-full text-xs font-bold border transition ${
              filters.status === s ? STATUS_STYLES[s] : 'border-gray-700 text-gray-500 hover:border-gray-500'
            }`}
          >
            {s.replace('_', ' ').toUpperCase()} ({statusCounts[s]})
          </button>
        ))}
      </div>

      {/* Filters */}
      <form onSubmit={applyFilters} className="bg-dark border border-gray-800 rounded-xl p-4 mb-6 flex flex-wrap gap-3 items-end">
        <div>
          <label className="text-xs text-gray-500 block mb-1">Date</label>
          <input
            type="date"
            value={filters.date}
            onChange={e => setFilters({ ...filters, date: e.target.value })}
            className="bg-darker border border-gray-700 rounded-lg px-3 py-2 text-white outline-none focus:border-primary text-sm"
          />
        </div>
        <div>
          <label className="text-xs text-gray-500 block mb-1">Status</label>
          <select
            value={filters.status}
            onChange={e => setFilters({ ...filters, status: e.target.value })}
            className="bg-darker border border-gray-700 rounded-lg px-3 py-2 text-white outline-none focus:border-primary text-sm"
          >
            <option value="">All Statuses</option>
            {ALL_STATUSES.map(s => <option key={s} value={s}>{s.replace('_', ' ')}</option>)}
          </select>
        </div>
        <button type="submit" className="bg-primary hover:bg-purple-600 text-white font-bold px-4 py-2 rounded-lg text-sm transition">
          🔍 Filter
        </button>
        <button type="button" onClick={clearFilters} className="border border-gray-700 text-gray-400 hover:text-white px-4 py-2 rounded-lg text-sm transition">
          Clear
        </button>
      </form>

      {/* Table */}
      {loading ? (
        <div className="text-center py-20 text-gray-500">Loading...</div>
      ) : bookings.length === 0 ? (
        <div className="text-center py-20 text-gray-600">No bookings found.</div>
      ) : (
        <>
          {/* Mobile Cards */}
          <div className="md:hidden space-y-4">
            {bookings.map(b => (
              <div key={b.id} className="bg-dark border border-gray-800 rounded-xl p-4">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <p className="font-bold">{b.service_detail?.name}</p>
                    <p className="text-xs text-gray-500 font-mono">{b.booking_id}</p>
                  </div>
                  <StatusBadge status={b.status} />
                </div>
                <p className="text-gray-400 text-sm">👤 {b.user_name || b.user_phone}</p>
                <p className="text-gray-400 text-sm">📅 {b.date} · 🕐 {b.time_display}</p>
                <p className="text-primary font-bold text-sm mt-1">₹{b.service_detail?.price}</p>
                <div className="mt-3">
                  <select
                    value={b.status}
                    disabled={updating === b.booking_id}
                    onChange={e => handleStatusChange(b.booking_id, e.target.value)}
                    className="w-full bg-darker border border-gray-700 rounded-lg px-3 py-2 text-white text-sm outline-none"
                  >
                    {ALL_STATUSES.map(s => <option key={s} value={s}>{s.replace('_', ' ')}</option>)}
                  </select>
                </div>
              </div>
            ))}
          </div>

          {/* Desktop Table */}
          <div className="hidden md:block bg-dark border border-gray-800 rounded-2xl overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-800">
                  {['Booking ID', 'Customer', 'Service', 'Date & Time', 'Amount', 'Status', 'Action'].map(h => (
                    <th key={h} className="text-left text-xs text-gray-500 font-bold px-4 py-3 uppercase tracking-wider">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {bookings.map((b, i) => (
                  <tr key={b.id} className={`border-b border-gray-800/50 hover:bg-white/2 transition ${i % 2 === 0 ? '' : 'bg-white/1'}`}>
                    <td className="px-4 py-3 font-mono text-xs text-primary">{b.booking_id}</td>
                    <td className="px-4 py-3">
                      <div className="font-medium text-sm">{b.user_name || '—'}</div>
                      <div className="text-gray-500 text-xs">{b.user_phone}</div>
                    </td>
                    <td className="px-4 py-3 text-sm">{b.service_detail?.name}</td>
                    <td className="px-4 py-3">
                      <div className="text-sm">{b.date}</div>
                      <div className="text-gray-500 text-xs">{b.time_display}</div>
                    </td>
                    <td className="px-4 py-3 text-primary font-bold text-sm">₹{b.service_detail?.price}</td>
                    <td className="px-4 py-3"><StatusBadge status={b.status} /></td>
                    <td className="px-4 py-3">
                      <select
                        value={b.status}
                        disabled={updating === b.booking_id}
                        onChange={e => handleStatusChange(b.booking_id, e.target.value)}
                        className="bg-darker border border-gray-700 rounded-lg px-2 py-1.5 text-white text-xs outline-none focus:border-primary disabled:opacity-50"
                      >
                        {ALL_STATUSES.map(s => <option key={s} value={s}>{s.replace('_', ' ')}</option>)}
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}

export default AdminBookings;