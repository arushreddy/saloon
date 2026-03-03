import axios from 'axios';

const API_BASE = 'http://127.0.0.1:8000/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

// Auto-attach JWT token to every request
api.interceptors.request.use((config) => {
  const tokens = JSON.parse(localStorage.getItem('tokens') || '{}');
  if (tokens.access) {
    config.headers.Authorization = `Bearer ${tokens.access}`;
  }
  return config;
});

// FIX #9: Prevent infinite refresh loop
// Old code: if refresh token also returns 401, it would call itself again forever
// Fix: use a flag on the request config to mark "already retried"
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Only attempt refresh once per request (prevent infinite loop)
    if (error.response?.status === 401 && !originalRequest._retried) {
      originalRequest._retried = true;

      const tokens = JSON.parse(localStorage.getItem('tokens') || '{}');

      if (tokens.refresh) {
        try {
          // Use plain axios (not the api instance) to avoid interceptor loop
          const res = await axios.post(`${API_BASE}/accounts/token/refresh/`, {
            refresh: tokens.refresh,
          });

          const newTokens = { ...tokens, access: res.data.access };
          localStorage.setItem('tokens', JSON.stringify(newTokens));

          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${res.data.access}`;
          return api(originalRequest);
        } catch (refreshError) {
          // Refresh token is also expired — force logout
          localStorage.removeItem('tokens');
          localStorage.removeItem('user');
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      } else {
        // No refresh token — redirect to login
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

// ── AUTH ──────────────────────────────────────
export const sendOTP = (phone) => api.post('/accounts/send-otp/', { phone });
export const verifyOTP = (phone, otp) => api.post('/accounts/verify-otp/', { phone, otp });
export const getProfile = () => api.get('/accounts/profile/');
export const updateProfile = (data) => api.put('/accounts/profile/update/', data);

// ── SERVICES ─────────────────────────────────
export const getServices = (showAll = false) =>
  api.get(`/services/${showAll ? '?all=true' : ''}`);
export const getServiceDetail = (id) => api.get(`/services/${id}/`);
export const getCategories = () => api.get('/services/categories/');

// ── BOOKINGS ─────────────────────────────────
export const getAvailableDates = () => api.get('/bookings/dates/');
export const getAvailableSlots = (date) => api.get(`/bookings/slots/?date=${date}`);
export const createBooking = (data) => api.post('/bookings/create/', data);
export const getMyBookings = (status) =>
  api.get(`/bookings/my/${status ? `?status=${status}` : ''}`);
export const cancelBooking = (bookingId) => api.post(`/bookings/${bookingId}/cancel/`);

// ── PAYMENTS ─────────────────────────────────
export const createPaymentOrder = (bookingId) =>
  api.post('/payments/create-order/', { booking_id: bookingId });
export const verifyPayment = (data) => api.post('/payments/verify/', data);
export const getPaymentStatus = (bookingId) => api.get(`/payments/status/${bookingId}/`);

// ── ADMIN ────────────────────────────────────
export const getAnalytics = () => api.get('/dashboard/analytics/');
export const adminGetBookings = (filters) =>
  api.get('/bookings/admin/all/', { params: filters });
export const adminUpdateSlot = (data) => api.post('/bookings/admin/slot/', data);
export const adminUpdateBookingStatus = (bookingId, status) =>
  api.put(`/bookings/admin/${bookingId}/status/`, { status });
export const adminCreateService = (data) => api.post('/services/create/', data);
export const adminUpdateService = (id, data) => api.put(`/services/${id}/update/`, data);
export const adminDeleteService = (id) => api.delete(`/services/${id}/delete/`);
export const adminGetPayments = (filters) =>
  api.get('/payments/admin/all/', { params: filters });

export default api;