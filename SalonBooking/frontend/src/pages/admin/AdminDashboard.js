import React from 'react';
import { Link } from 'react-router-dom';

function AdminDashboard() {
  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">⚙️ Admin <span className="text-gold">Dashboard</span></h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          { to: '/admin/services', icon: '💇', title: 'Services', desc: 'Manage salon services' },
          { to: '/admin/bookings', icon: '📋', title: 'Bookings', desc: 'View all bookings' },
          { to: '/admin/slots', icon: '📅', title: 'Slots', desc: 'Manage time slots' },
          { to: '/', icon: '🏠', title: 'Back to Site', desc: 'Return to main site' },
        ].map((item) => (
          <Link key={item.to} to={item.to} className="bg-dark border border-gray-800 rounded-2xl p-6 hover:border-primary transition group">
            <div className="text-4xl mb-3">{item.icon}</div>
            <h3 className="font-bold text-lg group-hover:text-primary transition">{item.title}</h3>
            <p className="text-gray-500 text-sm">{item.desc}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}

export default AdminDashboard;