import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { useAuth } from '../../context/AuthContext';
import { sendOTP, verifyOTP } from '../../services/api';

function Login() {
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [step, setStep] = useState('phone'); // 'phone' or 'otp'
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSendOTP = async (e) => {
    e.preventDefault();
    if (phone.length < 10) {
      toast.error('Enter a valid phone number');
      return;
    }
    setLoading(true);
    try {
      const res = await sendOTP(phone);
      toast.success('OTP sent!');
      // Dev mode: show OTP
      if (res.data.otp_debug) {
        toast.info(`Dev OTP: ${res.data.otp_debug}`, { autoClose: 10000 });
      }
      setStep('otp');
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to send OTP');
    }
    setLoading(false);
  };

  const handleVerifyOTP = async (e) => {
    e.preventDefault();
    if (otp.length !== 6) {
      toast.error('Enter 6-digit OTP');
      return;
    }
    setLoading(true);
    try {
      const res = await verifyOTP(phone, otp);
      toast.success('Login successful! 🎉');
      login(res.data.user, res.data.tokens);
      navigate('/');
    } catch (err) {
      toast.error(err.response?.data?.error || 'Invalid OTP');
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-darker flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        {/* Logo */}
        <div className="text-center mb-8">
          <span className="text-6xl">💈</span>
          <h1 className="text-3xl font-bold mt-4">
            Salon<span className="text-primary">Book</span>
          </h1>
          <p className="text-gray-500 mt-2">Book your perfect salon experience</p>
        </div>

        {/* Card */}
        <div className="bg-dark border border-gray-800 rounded-2xl p-8">
          {step === 'phone' ? (
            <>
              <h2 className="text-xl font-bold mb-1">Welcome! 👋</h2>
              <p className="text-gray-500 mb-6">Enter your phone number to continue</p>

              <form onSubmit={handleSendOTP}>
                <label className="block text-sm text-gray-400 mb-2">Phone Number</label>
                <div className="flex items-center bg-darker border border-gray-700 rounded-lg overflow-hidden focus-within:border-primary transition">
                  <span className="px-3 text-gray-500 bg-gray-800/50">+91</span>
                  <input
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value.replace(/\D/g, '').slice(0, 10))}
                    placeholder="9876543210"
                    className="flex-1 bg-transparent px-3 py-3 text-white outline-none text-lg"
                    maxLength={10}
                    autoFocus
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading || phone.length < 10}
                  className="w-full mt-6 bg-primary hover:bg-purple-600 disabled:bg-gray-700 disabled:text-gray-500 text-white font-bold py-3 rounded-lg transition text-lg"
                >
                  {loading ? '⏳ Sending...' : '📱 Send OTP'}
                </button>
              </form>
            </>
          ) : (
            <>
              <h2 className="text-xl font-bold mb-1">Verify OTP 🔐</h2>
              <p className="text-gray-500 mb-6">
                Enter the 6-digit code sent to <span className="text-primary">+91 {phone}</span>
              </p>

              <form onSubmit={handleVerifyOTP}>
                <label className="block text-sm text-gray-400 mb-2">OTP Code</label>
                <input
                  type="text"
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  placeholder="______"
                  className="w-full bg-darker border border-gray-700 rounded-lg px-4 py-3 text-white text-center text-2xl tracking-[0.5em] outline-none focus:border-primary transition"
                  maxLength={6}
                  autoFocus
                />

                <button
                  type="submit"
                  disabled={loading || otp.length !== 6}
                  className="w-full mt-6 bg-primary hover:bg-purple-600 disabled:bg-gray-700 disabled:text-gray-500 text-white font-bold py-3 rounded-lg transition text-lg"
                >
                  {loading ? '⏳ Verifying...' : '✅ Verify & Login'}
                </button>
              </form>

              <button
                onClick={() => { setStep('phone'); setOtp(''); }}
                className="w-full mt-3 text-gray-500 hover:text-primary transition text-sm"
              >
                ← Change phone number
              </button>
            </>
          )}
        </div>

        <p className="text-center text-gray-600 text-sm mt-6">
          By continuing, you agree to our Terms of Service
        </p>
      </div>
    </div>
  );
}

export default Login;