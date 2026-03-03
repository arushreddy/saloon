import React, { useState, useEffect, useRef } from 'react';
import { toast } from 'react-toastify';
// FIX #12: Import api at top level — never inside async functions (causes re-import on every call)
import api, { getServices, adminDeleteService } from '../../services/api';

const EMPTY_FORM = {
  name: '',
  description: '',
  price: '',
  duration_minutes: 60,
  category: '',
  is_active: true,
};

function ServiceModal({ service, onClose, onSave }) {
  const [form, setForm] = useState(service ? {
    name: service.name,
    description: service.description,
    price: service.price,
    duration_minutes: service.duration_minutes,
    category: service.category || '',
    is_active: service.is_active,
  } : EMPTY_FORM);
  const [imageFile, setImageFile] = useState(null);
  const [preview, setPreview] = useState(service?.image ? `http://127.0.0.1:8000${service.image}` : null);
  const [saving, setSaving] = useState(false);
  const fileRef = useRef();

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setImageFile(file);
    setPreview(URL.createObjectURL(file));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name || !form.price) {
      toast.error('Name and price are required');
      return;
    }
    setSaving(true);
    try {
      // Use FormData for image upload
      const fd = new FormData();
      Object.entries(form).forEach(([k, v]) => fd.append(k, v));
      if (imageFile) fd.append('image', imageFile);

      const tokens = JSON.parse(localStorage.getItem('tokens') || '{}');
      const headers = {
        'Content-Type': 'multipart/form-data',
        Authorization: `Bearer ${tokens.access}`,
      };

      let res;
      if (service) {
        res = await api.put(`/services/${service.id}/update/`, fd, { headers });
      } else {
        res = await api.post('/services/create/', fd, { headers });
      }

      toast.success(service ? 'Service updated!' : 'Service created!');
      onSave(res.data);
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to save service');
    }
    setSaving(false);
  };

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 px-4">
      <div className="bg-dark border border-gray-700 rounded-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-gray-800">
          <h2 className="text-xl font-bold">{service ? '✏️ Edit Service' : '➕ New Service'}</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-white text-2xl">✕</button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Image Upload */}
          <div>
            <label className="text-sm text-gray-400 block mb-2">Service Image</label>
            <div
              onClick={() => fileRef.current.click()}
              className="w-full h-40 border-2 border-dashed border-gray-700 hover:border-primary rounded-xl flex items-center justify-center cursor-pointer transition overflow-hidden"
            >
              {preview ? (
                <img src={preview} alt="preview" className="w-full h-full object-cover" />
              ) : (
                <div className="text-center text-gray-500">
                  <div className="text-4xl mb-2">📷</div>
                  <div className="text-sm">Click to upload image</div>
                </div>
              )}
            </div>
            <input ref={fileRef} type="file" accept="image/*" onChange={handleImageChange} className="hidden" />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className="text-sm text-gray-400 block mb-1">Service Name *</label>
              <input
                value={form.name}
                onChange={e => setForm({ ...form, name: e.target.value })}
                className="w-full bg-darker border border-gray-700 rounded-lg px-4 py-2.5 text-white outline-none focus:border-primary"
                placeholder="e.g. Classic Haircut"
              />
            </div>

            <div>
              <label className="text-sm text-gray-400 block mb-1">Price (₹) *</label>
              <input
                type="number"
                value={form.price}
                onChange={e => setForm({ ...form, price: e.target.value })}
                className="w-full bg-darker border border-gray-700 rounded-lg px-4 py-2.5 text-white outline-none focus:border-primary"
                placeholder="500"
              />
            </div>

            <div>
              <label className="text-sm text-gray-400 block mb-1">Duration (mins)</label>
              <input
                type="number"
                value={form.duration_minutes}
                onChange={e => setForm({ ...form, duration_minutes: parseInt(e.target.value) })}
                className="w-full bg-darker border border-gray-700 rounded-lg px-4 py-2.5 text-white outline-none focus:border-primary"
              />
            </div>

            <div className="col-span-2">
              <label className="text-sm text-gray-400 block mb-1">Category</label>
              <input
                value={form.category}
                onChange={e => setForm({ ...form, category: e.target.value })}
                className="w-full bg-darker border border-gray-700 rounded-lg px-4 py-2.5 text-white outline-none focus:border-primary"
                placeholder="e.g. Hair, Skin, Beard"
              />
            </div>

            <div className="col-span-2">
              <label className="text-sm text-gray-400 block mb-1">Description</label>
              <textarea
                value={form.description}
                onChange={e => setForm({ ...form, description: e.target.value })}
                rows={3}
                className="w-full bg-darker border border-gray-700 rounded-lg px-4 py-2.5 text-white outline-none focus:border-primary resize-none"
                placeholder="Describe the service..."
              />
            </div>

            <div className="col-span-2 flex items-center gap-3">
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.is_active}
                  onChange={e => setForm({ ...form, is_active: e.target.checked })}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-700 rounded-full peer peer-checked:bg-primary transition" />
                <div className="absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full transition peer-checked:translate-x-5" />
              </label>
              <span className="text-sm text-gray-300">Active (visible to customers)</span>
            </div>
          </div>

          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose}
              className="flex-1 border border-gray-700 hover:border-gray-500 text-gray-300 py-3 rounded-xl transition">
              Cancel
            </button>
            <button type="submit" disabled={saving}
              className="flex-1 bg-primary hover:bg-purple-600 disabled:bg-gray-700 text-white font-bold py-3 rounded-xl transition">
              {saving ? '⏳ Saving...' : service ? '💾 Update' : '✅ Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function AdminServices() {
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modal, setModal] = useState(null); // null | 'create' | service object

  useEffect(() => { fetchServices(); }, []);

  const fetchServices = async () => {
    try {
      // Get all including inactive — need admin endpoint
      const { default: api } = await import('../../services/api');
      const res = await api.get('/services/');
      setServices(res.data);
    } catch (err) {
      toast.error('Failed to load services');
    }
    setLoading(false);
  };

  const handleSave = (saved) => {
    setModal(null);
    fetchServices();
  };

  const handleDelete = async (service) => {
    if (!window.confirm(`Deactivate "${service.name}"?`)) return;
    try {
      await adminDeleteService(service.id);
      toast.success('Service deactivated');
      fetchServices();
    } catch (err) {
      toast.error('Failed to deactivate');
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold">💇 Service Management</h1>
          <p className="text-gray-500 text-sm mt-1">{services.length} services total</p>
        </div>
        <button
          onClick={() => setModal('create')}
          className="bg-primary hover:bg-purple-600 text-white font-bold px-5 py-2.5 rounded-xl transition"
        >
          ➕ Add Service
        </button>
      </div>

      {loading ? (
        <div className="text-center py-20 text-gray-500">Loading services...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {services.map(service => (
            <div key={service.id} className="bg-dark border border-gray-800 rounded-2xl overflow-hidden group">
              {/* Image */}
              <div className="h-40 bg-gray-800 overflow-hidden relative">
                {service.image ? (
                  <img
                    src={`http://127.0.0.1:8000${service.image}`}
                    alt={service.name}
                    className="w-full h-full object-cover group-hover:scale-105 transition duration-500"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-5xl">💇</div>
                )}
                {!service.is_active && (
                  <div className="absolute inset-0 bg-black/60 flex items-center justify-center">
                    <span className="bg-red-600 text-white text-xs font-bold px-3 py-1 rounded-full">INACTIVE</span>
                  </div>
                )}
              </div>

              <div className="p-4">
                <div className="flex justify-between items-start mb-1">
                  <h3 className="font-bold">{service.name}</h3>
                  <span className="text-primary font-bold">₹{service.price}</span>
                </div>
                {service.category && (
                  <span className="inline-block bg-primary/10 text-primary text-xs px-2 py-0.5 rounded mb-2">
                    {service.category}
                  </span>
                )}
                <p className="text-gray-500 text-sm line-clamp-2 mb-3">{service.description}</p>
                <div className="text-gray-600 text-xs mb-4">⏱ {service.duration_minutes} min</div>

                <div className="flex gap-2">
                  <button
                    onClick={() => setModal(service)}
                    className="flex-1 bg-primary/10 hover:bg-primary/20 text-primary font-bold py-2 rounded-lg text-sm transition"
                  >
                    ✏️ Edit
                  </button>
                  <button
                    onClick={() => handleDelete(service)}
                    className="flex-1 bg-red-500/10 hover:bg-red-500/20 text-red-400 font-bold py-2 rounded-lg text-sm transition"
                  >
                    🗑️ Deactivate
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal */}
      {modal && (
        <ServiceModal
          service={modal === 'create' ? null : modal}
          onClose={() => setModal(null)}
          onSave={handleSave}
        />
      )}
    </div>
  );
}

export default AdminServices;