import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'react-toastify';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts';
import { getAnalytics } from '../../services/api';

const STATUS_COLORS = {
  pending: '#F59E0B',
  confirmed: '#10B981',
  completed: '#3B82F6',
  cancelled: '#EF4444',
  no_show: '#6B7280',
};

const STAT_CARDS = [
  { key: 'total_users', label: 'Total Users', icon: '👥', color: 'text-blue-400', border: 'border-blue-500/30' },
  { key: 'total_bookings', label: 'Total Bookings', icon: '📋', color: 'text-purple-400', border: 'border-purple-500/30' },
  { key: 'today_bookings', label: "Today's Bookings", icon: '📅', color: 'text-green-400', border: 'border-green-500/30' },
  { key: 'total_services', label: 'Active Services', icon: '💇', color: 'text-yellow-400', border: 'border-yellow-500/30' },
];

function AdminDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { fetchAnalytics(); }, []);

  const fetchAnalytics = async () => {
    try {
      const res = await getAnalytics();
      setData(res.data);
    } catch (err) {
      toast.error('Failed to load analytics');
    }
    setLoading(false);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const pieData = (data?.status_breakdown || []).map(item => ({
    name: item.status.charAt(0).toUpperCase() + item.status.slice(1),
    value: item.count,
    color: STATUS_COLORS[item.status] || '#6B7280',
  }));

  const weeklyData = (data?.weekly_bookings || []).map(d => ({
    day: d.day.slice(0, 3),
    bookings: d.bookings,
  }));

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold">
            ⚙️ Admin <span className="text-yellow-400">Dashboard</span>
          </h1>
          <p className="text-gray-500 mt-1">Welcome back, salon owner 👋</p>
        </div>
        <button
          onClick={fetchAnalytics}
          className="bg-dark border border-gray-700 hover:border-primary text-gray-300 px-4 py-2 rounded-lg transition text-sm"
        >
          🔄 Refresh
        </button>
      </div>

      {/* Quick Nav */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {[
          { to: '/admin/services', icon: '💇', label: 'Services' },
          { to: '/admin/bookings', icon: '📋', label: 'Bookings' },
          { to: '/admin/slots', icon: '📅', label: 'Slots' },
          { to: '/', icon: '🏠', label: 'View Site' },
        ].map(item => (
          <Link
            key={item.to}
            to={item.to}
            className="bg-dark border border-gray-800 hover:border-primary rounded-xl p-4 text-center transition group"
          >
            <div className="text-2xl mb-1">{item.icon}</div>
            <div className="text-sm font-bold group-hover:text-primary transition">{item.label}</div>
          </Link>
        ))}
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {STAT_CARDS.map(card => (
          <div key={card.key} className={`bg-dark border ${card.border} rounded-2xl p-5`}>
            <div className="text-3xl mb-2">{card.icon}</div>
            <div className={`text-3xl font-bold ${card.color}`}>{data?.[card.key] ?? 0}</div>
            <div className="text-gray-500 text-sm mt-1">{card.label}</div>
          </div>
        ))}
      </div>

      {/* Revenue Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
        <div className="bg-dark border border-green-500/30 rounded-2xl p-6">
          <div className="text-gray-400 text-sm mb-1">💰 This Month Revenue</div>
          <div className="text-4xl font-bold text-green-400">
            ₹{parseFloat(data?.month_revenue || 0).toLocaleString('en-IN')}
          </div>
        </div>
        <div className="bg-dark border border-primary/30 rounded-2xl p-6">
          <div className="text-gray-400 text-sm mb-1">💎 Total Revenue</div>
          <div className="text-4xl font-bold text-primary">
            ₹{parseFloat(data?.total_revenue || 0).toLocaleString('en-IN')}
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        {/* Weekly Bar Chart */}
        <div className="bg-dark border border-gray-800 rounded-2xl p-6">
          <h3 className="font-bold mb-4 text-gray-300">📊 This Week's Bookings</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={weeklyData}>
              <XAxis dataKey="day" tick={{ fill: '#9CA3AF', fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#9CA3AF', fontSize: 12 }} axisLine={false} tickLine={false} allowDecimals={false} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #374151', borderRadius: 8, color: '#fff' }}
                cursor={{ fill: 'rgba(108,99,255,0.1)' }}
              />
              <Bar dataKey="bookings" fill="#6C63FF" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Pie Chart */}
        <div className="bg-dark border border-gray-800 rounded-2xl p-6">
          <h3 className="font-bold mb-4 text-gray-300">🥧 Booking Status</h3>
          {pieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  dataKey="value"
                  paddingAngle={3}
                >
                  {pieData.map((entry, index) => (
                    <Cell key={index} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #374151', borderRadius: 8, color: '#fff' }}
                />
                <Legend
                  formatter={(value) => <span style={{ color: '#9CA3AF', fontSize: 12 }}>{value}</span>}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-48 flex items-center justify-center text-gray-600">No booking data yet</div>
          )}
        </div>
      </div>

      {/* Popular Services */}
      <div className="bg-dark border border-gray-800 rounded-2xl p-6">
        <h3 className="font-bold mb-4 text-gray-300">🔥 Popular Services</h3>
        {data?.popular_services?.length > 0 ? (
          <div className="space-y-3">
            {data.popular_services.map((svc, i) => (
              <div key={i} className="flex items-center gap-4">
                <div className="w-8 h-8 bg-primary/20 rounded-full flex items-center justify-center text-primary font-bold text-sm">
                  {i + 1}
                </div>
                <div className="flex-1">
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-medium">{svc['service__name']}</span>
                    <span className="text-primary font-bold">{svc.count} bookings</span>
                  </div>
                  <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary rounded-full"
                      style={{ width: `${(svc.count / (data.popular_services[0]?.count || 1)) * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-600">No booking data yet. Services will appear here once bookings are made.</p>
        )}
      </div>
    </div>
  );
}

export default AdminDashboard;