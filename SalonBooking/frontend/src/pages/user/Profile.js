import React, { useState } from 'react';
import { toast } from 'react-toastify';
import { useAuth } from '../../context/AuthContext';
import { updateProfile } from '../../services/api';

function Profile() {
  const { user, login } = useAuth();
  const [name, setName] = useState(user?.name || '');
  const [email, setEmail] = useState(user?.email || '');
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      const res = await updateProfile({ name, email });
      const tokens = JSON.parse(localStorage.getItem('tokens'));
      login(res.data, tokens);
      toast.success('Profile updated!');
    } catch (err) { toast.error('Failed to update'); }
    setSaving(false);
  };

  return (
    <div className="max-w-lg mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">👤 My Profile</h1>
      <div className="bg-dark border border-gray-800 rounded-2xl p-6 space-y-4">
        <div>
          <label className="text-sm text-gray-400">Phone</label>
          <p className="text-lg font-bold text-primary">{user?.phone}</p>
        </div>
        <div>
          <label className="text-sm text-gray-400 block mb-1">Name</label>
          <input value={name} onChange={(e) => setName(e.target.value)}
            className="w-full bg-darker border border-gray-700 rounded-lg px-4 py-3 text-white outline-none focus:border-primary" />
        </div>
        <div>
          <label className="text-sm text-gray-400 block mb-1">Email</label>
          <input value={email} onChange={(e) => setEmail(e.target.value)} type="email"
            className="w-full bg-darker border border-gray-700 rounded-lg px-4 py-3 text-white outline-none focus:border-primary" />
        </div>
        <button onClick={handleSave} disabled={saving}
          className="w-full bg-primary hover:bg-purple-600 text-white font-bold py-3 rounded-lg transition">
          {saving ? 'Saving...' : '💾 Save Changes'}
        </button>
      </div>
    </div>
  );
}

export default Profile;