import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'react-toastify';
import { getServices } from '../../services/api';

function Home() {
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchServices();
  }, []);

  const fetchServices = async () => {
    try {
      const res = await getServices();
      setServices(res.data);
    } catch (err) {
      toast.error('Failed to load services');
    }
    setLoading(false);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Hero Section */}
      <div className="text-center mb-12">
        <h1 className="text-4xl md:text-5xl font-bold mb-4">
          Book Your Perfect <span className="text-primary">Salon Experience</span>
        </h1>
        <p className="text-gray-400 text-lg max-w-2xl mx-auto">
          Choose from our premium services, pick your preferred time slot, and enjoy a hassle-free booking experience.
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-3 gap-4 max-w-lg mx-auto mb-12">
        <div className="bg-dark border border-gray-800 rounded-xl p-4 text-center">
          <div className="text-2xl font-bold text-primary">{services.length}</div>
          <div className="text-gray-500 text-sm">Services</div>
        </div>
        <div className="bg-dark border border-gray-800 rounded-xl p-4 text-center">
          <div className="text-2xl font-bold text-green-400">12h</div>
          <div className="text-gray-500 text-sm">Daily Slots</div>
        </div>
        <div className="bg-dark border border-gray-800 rounded-xl p-4 text-center">
          <div className="text-2xl font-bold text-gold">5⭐</div>
          <div className="text-gray-500 text-sm">Rating</div>
        </div>
      </div>

      {/* Services Grid */}
      <h2 className="text-2xl font-bold mb-6">💇 Our Services</h2>

      {loading ? (
        <div className="text-center py-12 text-gray-500">Loading services...</div>
      ) : services.length === 0 ? (
        <div className="text-center py-12 text-gray-500">No services available yet.</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {services.map((service) => (
            <div key={service.id} className="bg-dark border border-gray-800 rounded-2xl overflow-hidden hover:border-primary transition group">
              {/* Image */}
              <div className="h-48 bg-gray-800 overflow-hidden">
                {service.image ? (
                  <img
                    src={`http://127.0.0.1:8000${service.image}`}
                    alt={service.name}
                    className="w-full h-full object-cover group-hover:scale-105 transition duration-500"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-4xl">💇</div>
                )}
              </div>

              {/* Content */}
              <div className="p-5">
                <div className="flex justify-between items-start mb-2">
                  <h3 className="text-lg font-bold">{service.name}</h3>
                  <span className="text-primary font-bold text-lg">₹{service.price}</span>
                </div>

                {service.category && (
                  <span className="inline-block bg-primary/10 text-primary text-xs px-2 py-1 rounded mb-3">
                    {service.category}
                  </span>
                )}

                <p className="text-gray-500 text-sm line-clamp-2 mb-4">
                  {service.description}
                </p>

                <div className="flex items-center justify-between">
                  <span className="text-gray-600 text-sm">⏱ {service.duration_minutes} min</span>
                  <Link
                    to={`/book/${service.id}`}
                    className="bg-primary hover:bg-purple-600 text-white px-5 py-2 rounded-lg font-bold text-sm transition"
                  >
                    Book Now →
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Home;