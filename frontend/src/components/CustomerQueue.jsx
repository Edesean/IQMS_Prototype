// frontend/src/components/CustomerQueue.jsx

import { useEffect, useState } from 'react';
import toast, { Toaster } from 'react-hot-toast';
import { Link } from 'react-router-dom';
import { getBranches, getServices, joinQueue } from '../services/api';
import { subscribeUser } from '../services/pushNotifications';

export default function CustomerQueue() {
  const [step, setStep] = useState('join');
  const [branches, setBranches] = useState([]);
  const [services, setServices] = useState([]);
  const [selectedBranch, setSelectedBranch] = useState('');
  const [selectedService, setSelectedService] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [ticket, setTicket] = useState(null);
  const [loading, setLoading] = useState(false);
  const [unavailableService, setUnavailableService] = useState(null);

  useEffect(() => {
    fetchBranches();
  }, []);

  const fetchBranches = async () => {
    try {
      const data = await getBranches();
      setBranches(data);
    } catch (err) {
      toast.error('Failed to load branches');
    }
  };

  const handleBranchChange = async (e) => {
    const branchId = e.target.value;
    setSelectedBranch(branchId);
    setSelectedService('');
    if (branchId) {
      try {
        const data = await getServices(branchId);
        setServices(data);
      } catch (err) {
        toast.error('Failed to load services');
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const selected = services.find((s) => s.id === selectedService);
    if (selected && !selected.is_active) {
      setUnavailableService(selected);
      return;
    }

    setLoading(true);
    try {
      const data = await joinQueue({
        branch_id: selectedBranch,
        service_category_id: selectedService,
        phone_number: phoneNumber,
        email: email,
        first_name: firstName,
        last_name: lastName,
      });
      setTicket(data);
      setStep('status');
      toast.success('Successfully joined the queue!');

      subscribeUser(phoneNumber).catch((err) =>
        console.warn('Push subscription skipped:', err)
      );
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to join queue');
    } finally {
      setLoading(false);
    }
  };

  const formatWaitTime = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    return `${minutes} minute${minutes !== 1 ? 's' : ''}`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center p-4">
      <Toaster position="top-center" />
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-blue-600">IQMS</h1>
          <p className="text-gray-500 text-sm mt-1">Intelligent Queue Management System</p>
        </div>

        {step === 'join' && (
          <>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-gray-700 text-sm font-semibold mb-2">
                  Select Branch
                </label>
                <select
                  className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={selectedBranch}
                  onChange={handleBranchChange}
                  required
                >
                  <option value="">-- Select a branch --</option>
                  {branches.map((branch) => (
                    <option key={branch.id} value={branch.id}>
                      {branch.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-gray-700 text-sm font-semibold mb-2">
                  Service Type
                </label>
                <select
                  className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={selectedService}
                  onChange={(e) => setSelectedService(e.target.value)}
                  required
                  disabled={!selectedBranch || services.length === 0}
                >
                  <option value="">-- Select a service --</option>
                  {services.map((service) => (
                    <option key={service.id} value={service.id}>
                      {service.name}{service.is_active ? '' : ' (Currently Unavailable)'}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-gray-700 text-xs font-semibold mb-2">
                    First Name (Optional)
                  </label>
                  <input
                    type="text"
                    className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                    placeholder="John"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-gray-700 text-xs font-semibold mb-2">
                    Last Name (Optional)
                  </label>
                  <input
                    type="text"
                    className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                    placeholder="Doe"
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                  />
                </div>
              </div>

              <div>
                <label className="block text-gray-700 text-sm font-semibold mb-2">
                  Email (for notifications)
                </label>
                <input
                  type="email"
                  className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
                <p className="text-xs text-gray-500 mt-1">
                  Get notified when your turn is approaching
                </p>
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
                  You will receive SMS notifications on this number
                </p>
              </div>

              <button
                type="submit"
                className="w-full bg-blue-600 text-white p-3 rounded-lg hover:bg-blue-700 transition font-semibold disabled:opacity-50"
                disabled={loading || !selectedBranch || !selectedService || !phoneNumber}
              >
                {loading ? 'Joining...' : 'Join Queue'}
              </button>
            </form>

            <div className="text-center mt-6">
              <Link to="/check-status" className="text-blue-600 text-sm underline">
                Already in a queue? Check your status →
              </Link>
            </div>
          </>
        )}

        {step === 'status' && ticket && (
          <div className="text-center space-y-4">
            {ticket.is_prebooking ? (
              <>
                <div className="bg-amber-50 border-2 border-amber-300 rounded-xl p-6">
                  <p className="text-2xl font-bold text-amber-700 mb-2">🌙 We're Closed</p>
                  <p className="text-gray-700 text-sm">
                    Business hours: <strong>8:00 AM – 4:00 PM (Mon-Fri)</strong>
                  </p>
                  <p className="text-gray-700 text-sm mt-3">
                    {ticket.message}
                  </p>
                </div>

                <div className="bg-blue-50 border-2 border-blue-200 rounded-xl p-6">
                  <p className="text-gray-600 text-sm">Your Pre-Booking Ticket</p>
                  <p className="text-3xl font-bold text-blue-600 my-3 break-all">
                    {ticket.ticket_number}
                  </p>
                  <p className="text-gray-600">
                    You are <span className="font-bold">#{ticket.queue_position}</span> in line
                  </p>
                </div>

                <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4">
                  <p className="text-sm text-yellow-800">
                    ⏰ Please come by <strong>8:30 AM</strong> — you'll be among the first customers served.
                  </p>
                </div>
              </>
            ) : (
              <>
                <div className="bg-green-50 border-2 border-green-200 rounded-xl p-6">
                  <p className="text-gray-600 text-sm">Your Ticket Number</p>
                  <p className="text-3xl font-bold text-green-600 my-3 break-all">
                    {ticket.ticket_number}
                  </p>
                  <p className="text-gray-600">
                    Position in Queue: <span className="font-bold">#{ticket.queue_position}</span>
                  </p>
                </div>

                <div className="bg-blue-50 border-2 border-blue-200 rounded-xl p-6">
                  <p className="text-gray-600 text-sm">Estimated Wait Time</p>
                  <p className="text-3xl font-bold text-blue-600 mt-2">
                    {formatWaitTime(ticket.estimated_wait_time)}
                  </p>
                </div>

                <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4">
                  <p className="text-sm text-yellow-800">
                    📱 You will receive a notification as your turn approaches.
                  </p>
                </div>
              </>
            )}

            <Link
              to="/check-status"
              className="w-full bg-blue-600 text-white p-3 rounded-lg hover:bg-blue-700 transition font-semibold block text-center"
            >
              🔍 Check My Status
            </Link>

            <button
              className="w-full border-2 border-gray-300 text-gray-700 p-3 rounded-lg hover:bg-gray-50 transition font-semibold"
              onClick={() => window.location.reload()}
            >
              Join Another Queue
            </button>
          </div>
        )}
      </div>

      {unavailableService && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-8 text-center">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-3xl">⚠️</span>
            </div>

            <h2 className="text-2xl font-bold text-gray-800 mb-2">
              Service Unavailable
            </h2>

            <p className="text-gray-600 mb-6">
              <strong className="text-red-600">"{unavailableService.name}"</strong> is currently unavailable at the moment. If you need assistance in another service kindly join with that service.
            </p>

            <button
              onClick={() => {
                setUnavailableService(null);
                setSelectedService('');
              }}
              className="w-full bg-blue-600 text-white p-3 rounded-lg hover:bg-blue-700 transition font-semibold"
            >
              Choose Another Service
            </button>

            <button
              onClick={() => window.location.reload()}
              className="w-full mt-3 text-gray-500 text-sm hover:text-gray-700 transition"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
