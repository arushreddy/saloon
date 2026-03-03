import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import { getAvailableDates, adminUpdateSlot } from '../../services/api';

function AdminSlots() {
  const [dates, setDates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(null); // date string being edited
  const [form, setForm] = useState({});
  const [saving, setSaving] = useState(false);

  useEffect(() => { fetchDates(); }, []);

  const fetchDates = async () => {
    try {
      const res = await getAvailableDates();
      setDates(res.data);
    } catch (err) {
      toast.error('Failed to load dates');
    }
    setLoading(false);
  };

  const startEdit = (date) => {
    setEditing(date.date);
    setForm({
      date: date.date,
      is_open: date.is_open ?? true,
      opening_hour: date.opening_hour ?? 9,
      closing_hour: date.closing_hour ?? 21,
      max_bookings_per_slot: date.max_bookings_per_slot ?? 5,
    });
  };

  const handleSave = async () => {
    if (form.opening_hour >= form.closing_hour) {
      toast.error('Opening hour must be before closing hour');
      return;
    }
    setSaving(true);
    try {
      await adminUpdateSlot(form);
      toast.success(`Slot configuration saved for ${form.date}`);
      setEditing(null);
      fetchDates();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to save slot config');
    }
    setSaving(false);
  };

  const quickToggle = async (date, isOpen) => {
    try {
      await adminUpdateSlot({
        date: date.date,
        is_open: isOpen,
        opening_hour: date.opening_hour ?? 9,
        closing_hour: date.closing_hour ?? 21,
        max_bookings_per_slot: date.max_bookings_per_slot ?? 5,
      });
      toast.success(isOpen ? `${date.date} is now OPEN` : `${date.date} is now CLOSED`);
      fetchDates();
    } catch (err) {
      toast.error('Failed to update');
    }
  };

  const hours = Array.from({ length: 24 }, (_, i) => i);
  const formatHour = (h) => {
    if (h === 0) return '12 AM';
    if (h < 12) return `${h} AM`;
    if (h === 12) return '12 PM';
    return `${h - 12} PM`;
  };

  // Group dates by week for calendar-style display
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold">📅 Slot Management</h1>
          <p className="text-gray-500 text-sm mt-1">Control which dates and hours are open for booking</p>
        </div>
        <button onClick={fetchDates} className="border border-gray-700 text-gray-400 hover:text-white px-4 py-2 rounded-lg text-sm transition">
          🔄 Refresh
        </button>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-6 mb-6 text-sm">
        <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-green-500" /> Open</div>
        <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-red-500" /> Closed</div>
        <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-gray-700" /> Default (open)</div>
      </div>

      {loading ? (
        <div className="text-center py-20 text-gray-500">Loading calendar...</div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {dates.map((d) => {
            const dateObj = new Date(d.date + 'T00:00:00');
            const isPast = dateObj < today;
            const isToday = d.date === today.toISOString().slice(0, 10);
            const isEditing = editing === d.date;

            return (
              <div
                key={d.date}
                className={`bg-dark border rounded-2xl overflow-hidden transition ${
                  isEditing
                    ? 'border-primary'
                    : isPast
                    ? 'border-gray-800 opacity-50'
                    : d.is_open
                    ? 'border-green-500/30'
                    : 'border-red-500/30'
                }`}
              >
                {/* Date Header */}
                <div className={`px-4 py-3 flex items-center justify-between ${
                  isToday ? 'bg-primary/20' : 'bg-gray-800/30'
                }`}>
                  <div>
                    <div className="font-bold text-sm">
                      {isToday && <span className="text-primary mr-1">TODAY</span>}
                      {dateObj.getDate()} {dateObj.toLocaleString('default', { month: 'short' })}
                    </div>
                    <div className="text-gray-500 text-xs">{d.day_name}</div>
                  </div>
                  <div className={`w-3 h-3 rounded-full ${d.is_open ? 'bg-green-500' : 'bg-red-500'}`} />
                </div>

                {/* Config Info */}
                {!isEditing ? (
                  <div className="p-4">
                    <div className="text-xs text-gray-500 space-y-1 mb-3">
                      <div>🕐 {formatHour(d.opening_hour ?? 9)} — {formatHour(d.closing_hour ?? 21)}</div>
                      <div>👥 Max {d.max_bookings_per_slot ?? 5} per slot</div>
                      <div className={d.is_open ? 'text-green-400' : 'text-red-400'}>
                        {d.is_open ? '✅ Open for bookings' : '🚫 Closed'}
                      </div>
                    </div>

                    {!isPast && (
                      <div className="flex gap-2">
                        <button
                          onClick={() => startEdit(d)}
                          className="flex-1 bg-primary/10 hover:bg-primary/20 text-primary text-xs font-bold py-1.5 rounded-lg transition"
                        >
                          ⚙️ Edit
                        </button>
                        <button
                          onClick={() => quickToggle(d, !d.is_open)}
                          className={`flex-1 text-xs font-bold py-1.5 rounded-lg transition ${
                            d.is_open
                              ? 'bg-red-500/10 hover:bg-red-500/20 text-red-400'
                              : 'bg-green-500/10 hover:bg-green-500/20 text-green-400'
                          }`}
                        >
                          {d.is_open ? '🚫 Close' : '✅ Open'}
                        </button>
                      </div>
                    )}
                  </div>
                ) : (
                  /* Edit Form */
                  <div className="p-4 space-y-3">
                    <div className="flex items-center gap-2">
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={form.is_open}
                          onChange={e => setForm({ ...form, is_open: e.target.checked })}
                          className="sr-only peer"
                        />
                        <div className="w-9 h-5 bg-gray-700 rounded-full peer peer-checked:bg-green-500 transition" />
                        <div className="absolute left-0.5 top-0.5 w-4 h-4 bg-white rounded-full transition peer-checked:translate-x-4" />
                      </label>
                      <span className="text-xs text-gray-300">{form.is_open ? 'Open' : 'Closed'}</span>
                    </div>

                    <div>
                      <label className="text-xs text-gray-500 block mb-1">Opens at</label>
                      <select
                        value={form.opening_hour}
                        onChange={e => setForm({ ...form, opening_hour: parseInt(e.target.value) })}
                        className="w-full bg-darker border border-gray-700 rounded-lg px-2 py-1.5 text-white text-xs outline-none"
                      >
                        {hours.map(h => <option key={h} value={h}>{formatHour(h)}</option>)}
                      </select>
                    </div>

                    <div>
                      <label className="text-xs text-gray-500 block mb-1">Closes at</label>
                      <select
                        value={form.closing_hour}
                        onChange={e => setForm({ ...form, closing_hour: parseInt(e.target.value) })}
                        className="w-full bg-darker border border-gray-700 rounded-lg px-2 py-1.5 text-white text-xs outline-none"
                      >
                        {hours.map(h => <option key={h} value={h}>{formatHour(h)}</option>)}
                      </select>
                    </div>

                    <div>
                      <label className="text-xs text-gray-500 block mb-1">Max bookings/slot</label>
                      <input
                        type="number"
                        min={1}
                        max={20}
                        value={form.max_bookings_per_slot}
                        onChange={e => setForm({ ...form, max_bookings_per_slot: parseInt(e.target.value) })}
                        className="w-full bg-darker border border-gray-700 rounded-lg px-2 py-1.5 text-white text-xs outline-none"
                      />
                    </div>

                    <div className="flex gap-2 pt-1">
                      <button
                        onClick={() => setEditing(null)}
                        className="flex-1 border border-gray-700 text-gray-400 text-xs py-1.5 rounded-lg hover:border-gray-500 transition"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={handleSave}
                        disabled={saving}
                        className="flex-1 bg-primary text-white text-xs font-bold py-1.5 rounded-lg hover:bg-purple-600 disabled:opacity-50 transition"
                      >
                        {saving ? '...' : '💾 Save'}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Bulk Actions Note */}
      <div className="mt-8 bg-dark border border-gray-800 rounded-xl p-4 text-gray-500 text-sm">
        <strong className="text-gray-400">💡 Tips:</strong>
        <ul className="mt-2 space-y-1 list-disc list-inside">
          <li>Closing a date prevents new bookings but doesn't cancel existing ones.</li>
          <li>Default hours are 9 AM – 9 PM with 5 bookings per slot.</li>
          <li>Changes take effect immediately for new bookings.</li>
        </ul>
      </div>
    </div>
  );
}

export default AdminSlots;