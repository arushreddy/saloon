import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

function Navbar() {
  const { user, isAdmin, logout } = useAuth();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="bg-dark border-b border-gray-800 px-4 py-3 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2">
          <span className="text-2xl">💈</span>
          <span className="text-xl font-bold text-white">
            Salon<span className="text-primary">Book</span>
          </span>
        </Link>

        {/* Desktop Menu */}
        <div className="hidden md:flex items-center gap-6">
          <Link to="/" className="text-gray-300 hover:text-primary transition">
            🏠 Home
          </Link>
          <Link to="/my-bookings" className="text-gray-300 hover:text-primary transition">
            📋 My Bookings
          </Link>
          <Link to="/profile" className="text-gray-300 hover:text-primary transition">
            👤 Profile
          </Link>

          {isAdmin && (
            <>
              <div className="w-px h-6 bg-gray-700" />
              <Link to="/admin" className="text-gold hover:text-yellow-300 transition">
                ⚙️ Admin
              </Link>
            </>
          )}

          <div className="w-px h-6 bg-gray-700" />
          <span className="text-gray-500 text-sm">{user?.phone}</span>
          <button
            onClick={handleLogout}
            className="bg-red-600/20 text-red-400 px-3 py-1 rounded hover:bg-red-600/40 transition text-sm"
          >
            Logout
          </button>
        </div>

        {/* Mobile menu button */}
        <button
          className="md:hidden text-gray-300 text-2xl"
          onClick={() => setMenuOpen(!menuOpen)}
        >
          {menuOpen ? '✕' : '☰'}
        </button>
      </div>

      {/* Mobile Menu */}
      {menuOpen && (
        <div className="md:hidden mt-3 pb-3 border-t border-gray-800 pt-3 flex flex-col gap-3">
          <Link to="/" onClick={() => setMenuOpen(false)} className="text-gray-300 hover:text-primary px-2">🏠 Home</Link>
          <Link to="/my-bookings" onClick={() => setMenuOpen(false)} className="text-gray-300 hover:text-primary px-2">📋 My Bookings</Link>
          <Link to="/profile" onClick={() => setMenuOpen(false)} className="text-gray-300 hover:text-primary px-2">👤 Profile</Link>
          {isAdmin && <Link to="/admin" onClick={() => setMenuOpen(false)} className="text-gold hover:text-yellow-300 px-2">⚙️ Admin Panel</Link>}
          <button onClick={handleLogout} className="text-red-400 text-left px-2">🚪 Logout</button>
        </div>
      )}
    </nav>
  );
}

export default Navbar;