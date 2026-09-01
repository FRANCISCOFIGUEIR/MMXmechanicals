import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import './i18n/config';
import './styles/globals.css';
import AppLayout from './components/layout/AppLayout';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import GeometryLibrary from './pages/GeometryLibrary';
import SimulationNew from './pages/SimulationNew';
import SimulationResults from './pages/SimulationResults';
import { useEffect, useState } from 'react';
function AuthGuard({ children }) {
  const location = useLocation();
  const [checking, setChecking] = useState(true);
  const [authed, setAuthed] = useState(false);
  useEffect(() => { setAuthed(!!localStorage.getItem('mmx_token')); setChecking(false); }, []);
  if (checking) return <div className="min-h-screen bg-mmx-bg flex items-center justify-center"><div className="w-12 h-12 rounded-full border-4 border-mmx-border border-t-mmx-accent animate-spin" /></div>;
  if (!authed && location.pathname !== '/login') return <Navigate to="/login" replace />;
  if (authed && location.pathname === '/login') return <Navigate to="/" replace />;
  return children;
}
export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<AuthGuard><Login /></AuthGuard>} />
        <Route path="/*" element={<AuthGuard><AppLayout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/library" element={<GeometryLibrary />} />
            <Route path="/simulation/new" element={<SimulationNew />} />
            <Route path="/simulation/:id" element={<SimulationResults />} />
            <Route path="/projects" element={<Dashboard />} />
            <Route path="/simulations" element={<Dashboard />} />
            <Route path="/settings" element={<Dashboard />} />
          </Routes>
        </AppLayout></AuthGuard>} />
      </Routes>
    </BrowserRouter>
  );
}