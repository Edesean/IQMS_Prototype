import { BrowserRouter, Route, Routes } from 'react-router-dom';
import CheckStatus from './components/CheckStatus';
import CustomerQueue from './components/CustomerQueue';
import Login from './components/Login';
import ManagerDashboard from './components/ManagerDashboard';
import TellerDashboard from './components/TellerDashboard';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<CustomerQueue />} />
        <Route path="/check-status" element={<CheckStatus />} />
        <Route path="/login" element={<Login />} />
        <Route path="/teller" element={<TellerDashboard />} />
        <Route path="/manager" element={<ManagerDashboard />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;