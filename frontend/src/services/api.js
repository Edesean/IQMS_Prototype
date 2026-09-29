// frontend/src/services/api.js

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://iqms-backend-raf7.onrender.com/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// List of public endpoints that should NOT require a token
const PUBLIC_PATHS = ['/branches/', '/services/', '/login/', '/join/', '/check-status/', '/cancel-ticket/', '/subscribe-push/'];

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  const isPublic = PUBLIC_PATHS.some((path) => config.url?.includes(path));
  if (token && !isPublic) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Authentication
export const login = async (email, password) => {
  const response = await api.post('/login/', { email, password });
  if (response.data.access) {
    localStorage.setItem('access_token', response.data.access);
    localStorage.setItem('refresh_token', response.data.refresh);
    localStorage.setItem('user', JSON.stringify(response.data.user));
  }
  return response.data;
};

export const logout = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
  window.location.href = '/';
};

export const getCurrentUser = () => {
  const user = localStorage.getItem('user');
  return user ? JSON.parse(user) : null;
};

// Customer endpoints
export const joinQueue = async (data) => {
  const response = await api.post('/join/', data);
  return response.data;
};

export const checkStatus = async (ticketNumber, phoneNumber) => {
  const response = await api.post('/check-status/', {
    ticket_number: ticketNumber,
    phone_number: phoneNumber,
  });
  return response.data;
};

// Teller endpoints
export const callNext = async () => {
  const response = await api.post('/call-next/');
  return response.data;
};

export const startService = async (ticketId) => {
  const response = await api.post('/start-service/', { ticket_id: ticketId });
  return response.data;
};

export const completeService = async (ticketId) => {
  const response = await api.post('/complete-service/', { ticket_id: ticketId });
  return response.data;
};

export const getQueueStatus = async () => {
  const response = await api.get('/queue-status/');
  return response.data;
};

export const getAnalytics = async (range = 'today') => {
  const response = await api.get(`/analytics/?range=${range}`);
  return response.data;
};

// Public endpoints (no auth needed)
export const getBranches = async () => {
  const response = await api.get('/branches/');
  return response.data;
};

export const getServices = async (branchId) => {
  const response = await api.get(`/services/?branch=${branchId}`);
  return response.data;
};

export default api;

export const cancelTicket = async (ticketNumber, phoneNumber) => {
  const response = await api.post('/cancel-ticket/', {
    ticket_number: ticketNumber,
    phone_number: phoneNumber,
  });
  return response.data;
};

export const markNoShow = async (ticketId) => {
  const response = await api.post('/no-show/', { ticket_id: ticketId });
  return response.data;
};