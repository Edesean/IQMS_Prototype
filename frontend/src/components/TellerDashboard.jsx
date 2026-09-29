// frontend/src/components/TellerDashboard.jsx

import { useEffect, useState } from 'react';
import toast, { Toaster } from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';
import {
  callNext,
  completeService,
  getCurrentUser,
  getQueueStatus,
  logout,
  markNoShow,
  startService,
} from '../services/api';

export default function TellerDashboard() {
  const [currentTicket, setCurrentTicket] = useState(null);
  const [queueCount, setQueueCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const user = getCurrentUser();
  const navigate = useNavigate();

  useEffect(() => {
    if (!user || user.role !== 'teller') {
      navigate('/login');
      return;
    }
    fetchStatus();
    const interval = setInterval(fetchStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchStatus = async () => {
    try {
      const data = await getQueueStatus();
      setQueueCount(data.waiting_count || 0);
      setCurrentTicket(data.current_ticket);
    } catch (err) {
      console.error('Failed to fetch status:', err);
    }
  };

  const handleCallNext = async () => {
    setLoading(true);
    try {
      const data = await callNext();
      setCurrentTicket(data);
      setQueueCount((c) => Math.max(c - 1, 0));
      toast.success(`Called ${data.ticket_number}`);
    } catch (err) {
      if (err.response?.status === 404) {
        toast('No customers waiting', { icon: 'ℹ️' });
      } else {
        toast.error('Failed to call next customer');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleStartService = async () => {
    if (!currentTicket) return;
    try {
      await startService(currentTicket.id);
      setCurrentTicket({ ...currentTicket, status: 'serving' });
      toast.success('Service started');
    } catch (err) {
      toast.error('Failed to start service');
    }
  };

  const handleCompleteService = async () => {
    if (!currentTicket) return;
    try {
      await completeService(currentTicket.id);
      toast.success('Service completed!');
      setCurrentTicket(null);
      fetchStatus();
    } catch (err) {
      toast.error('Failed to complete service');
    }
  };

  const handleNoShow = async () => {
  if (!currentTicket) return;
  if (!window.confirm('Mark this customer as no-show?')) return;
  try {
    await markNoShow(currentTicket.id);
    toast.success('Marked as no-show');
    setCurrentTicket(null);
    fetchStatus();
  } catch (err) {
    toast.error(err.response?.data?.error || 'Failed to mark no-show');
  }
};

  const handleLogout = () => {
    logout();
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <Toaster position="top-center" />

      <div className="bg-blue-600 text-white p-4 shadow-lg">
        <div className="max-w-4xl mx-auto flex justify-between items-center">
                    <div>
            <h1 className="text-xl font-bold">IQMS - Teller Dashboard</h1>
            <p className="text-sm text-blue-200">
              Welcome, {user?.full_name}
              {user?.service_category_names?.length > 0 ? (
                <span className="ml-2 bg-blue-500 px-2 py-0.5 rounded text-xs">
                  {user.service_category_names.join(' • ')}
                </span>
              ) : (
                <span className="ml-2 bg-blue-500 px-2 py-0.5 rounded text-xs">
                  All Services
                </span>
              )}
            </p>
          </div>
          <button
            onClick={handleLogout}
            className="bg-blue-700 px-4 py-2 rounded hover:bg-blue-800 transition"
          >
            Logout
          </button>
        </div>
      </div>

      <div className="max-w-4xl mx-auto p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-white p-4 rounded-lg shadow">
            <p className="text-gray-500 text-sm">Waiting Customers</p>
            <p className="text-3xl font-bold text-blue-600">{queueCount}</p>
          </div>
          <div className="bg-white p-4 rounded-lg shadow">
            <p className="text-gray-500 text-sm">Current Ticket</p>
            <p className="text-3xl font-bold">
              {currentTicket?.ticket_number || '—'}
            </p>
          </div>
          <div className="bg-white p-4 rounded-lg shadow">
            <p className="text-gray-500 text-sm">Status</p>
            <p className="text-3xl font-bold capitalize">
              {currentTicket?.status || 'Idle'}
            </p>
          </div>
        </div>

        {currentTicket && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-lg font-bold mb-4">Current Customer</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-gray-500 text-sm">Ticket</p>
                <p className="text-2xl font-bold">{currentTicket.ticket_number}</p>
              </div>
              <div>
                <p className="text-gray-500 text-sm">Service</p>
                <p className="text-xl">{currentTicket.service_name || currentTicket.service_category}</p>
              </div>
              <div>
                <p className="text-gray-500 text-sm">Customer</p>
                <p className="text-xl">{currentTicket.customer_name || 'Customer'}</p>
              </div>
              <div>
                <p className="text-gray-500 text-sm">Joined At</p>
                <p className="text-xl">
                  {currentTicket.joined_at
                    ? new Date(currentTicket.joined_at).toLocaleTimeString()
                    : '—'}
                </p>
              </div>
            </div>
          </div>
        )}

        <div className="flex gap-4 flex-wrap">
          <button
            className="bg-blue-600 text-white p-3 rounded-lg hover:bg-blue-700 transition flex-1 min-w-[150px] disabled:opacity-50 font-semibold"
            onClick={handleCallNext}
            disabled={loading || queueCount === 0 || currentTicket}
          >
            {loading ? 'Loading...' : '📞 Call Next Customer'}
          </button>

          {currentTicket?.status === 'called' && (
  <>
    <button
      className="bg-green-600 text-white p-3 rounded-lg hover:bg-green-700 transition flex-1 min-w-[150px] font-semibold"
      onClick={handleStartService}
    >
      🟢 Start Service
    </button>
    <button
      className="bg-red-500 text-white p-3 rounded-lg hover:bg-red-600 transition flex-1 min-w-[150px] font-semibold"
      onClick={handleNoShow}
    >
      ⏭️ No Show
    </button>
  </>
)}

          {currentTicket?.status === 'serving' && (
            <button
              className="bg-red-600 text-white p-3 rounded-lg hover:bg-red-700 transition flex-1 min-w-[150px] font-semibold"
              onClick={handleCompleteService}
            >
              ✅ Complete Service
            </button>
          )}
        </div>
      </div>
    </div>
  );
}