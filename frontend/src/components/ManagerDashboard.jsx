// frontend/src/components/ManagerDashboard.jsx

import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Title,
  Tooltip,
} from 'chart.js';
import { useEffect, useState } from 'react';
import { Bar, Line } from 'react-chartjs-2';
import toast, { Toaster } from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';
import { getAnalytics, getCurrentUser, logout } from '../services/api';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend
);

export default function ManagerDashboard() {
  const [stats, setStats] = useState({
    total_tickets: 0,
    completed_count: 0,
    cancelled_count: 0,
    average_wait_time: 0,
    average_service_time: 0,
    abandonment_rate: 0,
  });
  const [waitTimeChart, setWaitTimeChart] = useState({ labels: [], data: [] });
  const [serviceTimeChart, setServiceTimeChart] = useState({ labels: [], data: [] });
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState('today');
  const user = getCurrentUser();
  const navigate = useNavigate();

  useEffect(() => {
    if (!user || (user.role !== 'manager' && user.role !== 'admin')) {
      navigate('/login');
      return;
    }
    fetchAnalytics();
  }, [dateRange]);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const data = await getAnalytics(dateRange);
      setStats(data.stats);
      setWaitTimeChart(data.wait_time_chart || { labels: [], data: [] });
      setServiceTimeChart(data.service_time_chart || { labels: [], data: [] });
    } catch (err) {
      toast.error('Failed to fetch analytics');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
  };

  const formatTime = (seconds) => {
    if (!seconds || seconds === 0) return '0m';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}m ${secs}s`;
  };

  const barData = {
    labels: waitTimeChart.labels,
    datasets: [
      {
        label: 'Avg Wait Time (minutes)',
        data: waitTimeChart.data,
        backgroundColor: 'rgba(59, 130, 246, 0.6)',
        borderColor: 'rgba(59, 130, 246, 1)',
        borderWidth: 1,
      },
    ],
  };

  const lineData = {
    labels: serviceTimeChart.labels,
    datasets: [
      {
        label: 'Avg Service Time (minutes)',
        data: serviceTimeChart.data,
        borderColor: 'rgba(34, 197, 94, 1)',
        backgroundColor: 'rgba(34, 197, 94, 0.2)',
        tension: 0.4,
        fill: true,
      },
    ],
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <Toaster position="top-center" />

      <div className="bg-blue-600 text-white p-4 shadow-lg">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <div>
            <h1 className="text-xl font-bold">IQMS - Manager Dashboard</h1>
            <p className="text-sm text-blue-200">Welcome, {user?.full_name}</p>
          </div>
          <button
            onClick={handleLogout}
            className="bg-blue-700 px-4 py-2 rounded hover:bg-blue-800 transition"
          >
            Logout
          </button>
        </div>
      </div>

      <div className="max-w-6xl mx-auto p-4">
        <div className="flex justify-end mb-4">
          <select
            className="border rounded p-2 bg-white"
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value)}
          >
            <option value="today">Today</option>
            <option value="week">This Week</option>
            <option value="month">This Month</option>
          </select>
        </div>

        {loading ? (
          <div className="flex justify-center items-center h-64">Loading...</div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
              <div className="bg-white p-4 rounded-lg shadow">
                <p className="text-gray-500 text-sm">Total Customers</p>
                <p className="text-2xl font-bold">{stats.total_tickets}</p>
              </div>
              <div className="bg-white p-4 rounded-lg shadow">
                <p className="text-gray-500 text-sm">Completed</p>
                <p className="text-2xl font-bold text-green-600">{stats.completed_count}</p>
              </div>
              <div className="bg-white p-4 rounded-lg shadow">
                <p className="text-gray-500 text-sm">Avg Wait Time</p>
                <p className="text-2xl font-bold text-blue-600">{formatTime(stats.average_wait_time)}</p>
              </div>
              <div className="bg-white p-4 rounded-lg shadow">
                <p className="text-gray-500 text-sm">Avg Service Time</p>
                <p className="text-2xl font-bold text-green-600">{formatTime(stats.average_service_time)}</p>
              </div>
              <div className="bg-white p-4 rounded-lg shadow">
                <p className="text-gray-500 text-sm">Abandonment Rate</p>
                <p className="text-2xl font-bold text-red-600">
                  {stats.abandonment_rate?.toFixed(1) || '0'}%
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white p-4 rounded-lg shadow">
                <h3 className="font-bold mb-4">Wait Time by Hour</h3>
                <Bar data={barData} options={{ responsive: true, maintainAspectRatio: true }} />
              </div>
              <div className="bg-white p-4 rounded-lg shadow">
                <h3 className="font-bold mb-4">Service Time Trend</h3>
                <Line data={lineData} options={{ responsive: true, maintainAspectRatio: true }} />
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}