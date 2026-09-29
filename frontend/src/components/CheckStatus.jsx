// frontend/src/components/CheckStatus.jsx

import { useCallback, useEffect, useState } from 'react';
import toast, { Toaster } from 'react-hot-toast';
import { Link } from 'react-router-dom';
import { cancelTicket, checkStatus } from '../services/api';

export default function CheckStatus() {
  const [ticketNumber, setTicketNumber] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [tracking, setTracking] = useState(false);

  const fetchStatus = useCallback(async () => {
    try {
      const data = await checkStatus(ticketNumber, phoneNumber);
      setStatus(data);
      setLastUpdated(new Date());
    } catch (err) {
      if (err.response?.status === 404) {
        toast.error('No ticket found with those details');
      } else {
        toast.error('Failed to fetch status');
      }
      setTracking(false);
    }
  }, [ticketNumber, phoneNumber]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setStatus(null);

    try {
      const data = await checkStatus(ticketNumber, phoneNumber);
      setStatus(data);
      setLastUpdated(new Date());
      setTracking(true);
      toast.success('Status loaded');
    } catch (err) {
      if (err.response?.status === 404) {
        toast.error('No ticket found. Check your ticket number and phone number.');
      } else {
        toast.error('Something went wrong. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  // Auto-refresh every 15 seconds while tracking
  useEffect(() => {
    if (!tracking || !status) return;
    // Stop refreshing if the ticket is done
    if (['completed', 'cancelled', 'serving'].includes(status.status)) return;

    const interval = setInterval(fetchStatus, 15000);
    return () => clearInterval(interval);
  }, [tracking, status, fetchStatus]);

  const formatWaitTime = (seconds) => {
    if (!seconds || seconds === 0) return '0 minutes';
    const minutes = Math.floor(seconds / 60);
    return `${minutes} minute${minutes !== 1 ? 's' : ''}`;
  };

  const handleReset = () => {
    setStatus(null);
    setTicketNumber('');
    setPhoneNumber('');
    setTracking(false);
    setLastUpdated(null);
  };

  const statusColor = {
    waiting: 'bg-blue-50 border-blue-200',
    called: 'bg-yellow-50 border-yellow-200',
    serving: 'bg-purple-50 border-purple-200',
    completed: 'bg-green-50 border-green-200',
    cancelled: 'bg-red-50 border-red-200',
  };

  const statusLabel = {
    waiting: 'Waiting in Queue',
    called: 'Your Turn!',
    serving: 'Being Served',
    completed: 'Completed',
    cancelled: 'Cancelled',
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center p-4">
      <Toaster position="top-center" />
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-blue-600">Check Your Status</h1>
          <p className="text-gray-500 text-sm mt-1">
            Enter your ticket number and phone number
          </p>
        </div>

        {!status && (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-gray-700 text-sm font-semibold mb-2">
                Ticket Number
              </label>
              <input
                type="text"
                className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 uppercase"
                placeholder="e.g., C-0001"
                value={ticketNumber}
                onChange={(e) => setTicketNumber(e.target.value.toUpperCase())}
                required
              />
            </div>

            <div>
              <label className="block text-gray-700 text-sm font-semibold mb-2">
                Phone Number
              </label>
              <input
                type="tel"
                className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="080xxxxxxxx"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                required
              />
              <p className="text-xs text-gray-500 mt-1">
                The phone number you used to join the queue
              </p>
            </div>

            <button
              type="submit"
              className="w-full bg-blue-600 text-white p-3 rounded-lg hover:bg-blue-700 transition font-semibold disabled:opacity-50"
              disabled={loading || !ticketNumber || !phoneNumber}
            >
              {loading ? 'Checking...' : 'Check Status'}
            </button>
          </form>
        )}

        {status && (
          <div className="space-y-4">
            <div className={`border-2 rounded-xl p-6 text-center ${statusColor[status.status] || 'bg-gray-50 border-gray-200'}`}>
              <p className="text-sm text-gray-600">{statusLabel[status.status] || status.status}</p>
              <p className="text-4xl font-bold text-gray-800 my-3">{status.ticket_number}</p>
              <p className="text-gray-600 text-sm">{status.branch}</p>
              <p className="text-gray-500 text-xs">{status.service_category}</p>
            </div>

            {status.status === 'waiting' && (
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-blue-50 border-2 border-blue-200 rounded-xl p-4 text-center">
                  <p className="text-xs text-gray-600">Position</p>
                  <p className="text-3xl font-bold text-blue-600">
                    #{status.queue_position}
                  </p>
                </div>
                <div className="bg-indigo-50 border-2 border-indigo-200 rounded-xl p-4 text-center">
                  <p className="text-xs text-gray-600">Est. Wait</p>
                  <p className="text-3xl font-bold text-indigo-600">
                    {Math.floor(status.estimated_wait_time / 60)}m
                  </p>
                </div>
              </div>
            )}

            {status.message && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4">
                <p className="text-sm text-yellow-800 text-center">{status.message}</p>
              </div>
            )}

            {lastUpdated && (
              <p className="text-xs text-gray-400 text-center">
                Last updated: {lastUpdated.toLocaleTimeString()}
                {['waiting', 'called'].includes(status.status) && ' • Auto-refreshing every 15s'}
              </p>
            )}
            {status.status === 'waiting' && (
  <button
    onClick={async () => {
      if (!window.confirm('Are you sure you want to cancel this ticket?')) return;
      try {
        const res = await cancelTicket(ticketNumber, phoneNumber);
        toast.success(res.message || 'Ticket cancelled');
        setTimeout(() => handleReset(), 1000);
      } catch (err) {
        toast.error(err.response?.data?.error || 'Failed to cancel ticket');
      }
    }}
    className="w-full border-2 border-red-500 text-red-500 p-3 rounded-lg hover:bg-red-50 transition font-semibold"
  >
    ❌ Cancel My Ticket
  </button>
)}
            <button
              onClick={handleReset}
              className="w-full border-2 border-gray-300 text-gray-700 p-3 rounded-lg hover:bg-gray-50 transition font-semibold"
            >
              Check Another Ticket
            </button>
          </div>
)}

        <div className="mt-6 text-center">
          <Link to="/" className="text-blue-600 text-sm underline">
            ← Back to Join Queue
          </Link>
        </div>
      </div>
    </div>
  );
}