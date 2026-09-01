import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mail, Lock, ArrowRight, Eye, EyeOff } from 'lucide-react';
import { AuthAPI } from '../services/api';
export default function Login() {
  const navigate = useNavigate();
  const [mode, setMode] = useState('login');
  const [email, setEmail] = useState(''); const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState(''); const [company, setCompany] = useState('');
  const [showPwd, setShowPwd] = useState(false); const [loading, setLoading] = useState(false); const [error, setError] = useState('');
  const handleSubmit = async (e) => {
    e.preventDefault(); setLoading(true); setError('');
    try {
      const { data } = mode === 'login' ? await AuthAPI.login(email, password) : await AuthAPI.register(email, password, fullName, company);
      localStorage.setItem('mmx_token', data.access_token); localStorage.setItem('mmx_refresh', data.refresh_token); navigate('/');
    } catch (err) { setError(err.response?.data?.detail || 'Erro'); } finally { setLoading(false); }
  };
  return (
    <div className="min-h-screen bg-mmx-bg flex">
      <div className="fixed inset-0 grid-bg opacity-20 pointer-events-none" />
      <div className="hidden lg:flex flex-col justify-center w-1/2 px-16 relative z-10">
        <div className="flex items-center gap-3 mb-8"><div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-mmx-accent to-mmx-accent-2 flex items-center justify-center font-bold text-mmx-bg text-xl">MX</div><h1 className="font-display font-bold text-2xl">MMX <span className="gradient-text">Mechanics</span></h1></div>
        <h2 className="font-display text-4xl font-bold mb-4">Fluidodinamica Computacional<br /><span className="gradient-text">na velocidade da GPU</span></h2>
        <p className="text-mmx-muted text-lg mb-8 max-w-md">Simulacao de escoamento e transferencia de calor com Lattice Boltzmann Method acelerado por CUDA.</p>
      </div>
      <div className="flex-1 flex items-center justify-center px-6 relative z-10">
        <div className="w-full max-w-md">
          <div className="glass-strong rounded-3xl p-8">
            <div className="flex gap-2 mb-6 p-1 bg-mmx-surface rounded-xl">
              <button onClick={() => setMode('login')} className={`flex-1 py-2.5 rounded-lg text-sm font-semibold ${mode === 'login' ? 'bg-mmx-accent text-mmx-bg' : 'text-mmx-muted'}`}>Entrar</button>
              <button onClick={() => setMode('register')} className={`flex-1 py-2.5 rounded-lg text-sm font-semibold ${mode === 'register' ? 'bg-mmx-accent text-mmx-bg' : 'text-mmx-muted'}`}>Criar Conta</button>
            </div>
            {error && <div className="mb-4 p-3 rounded-xl bg-mmx-danger/10 border border-mmx-danger/20 text-mmx-danger text-sm">{error}</div>}
            <form onSubmit={handleSubmit} className="space-y-4">
              {mode === 'register' && <input type="text" value={fullName} onChange={e => setFullName(e.target.value)} placeholder="Nome completo" className="input-mmx" required />}
              {mode === 'register' && <input type="text" value={company} onChange={e => setCompany(e.target.value)} placeholder="Empresa" className="input-mmx" />}
              <div className="relative"><Mail size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-mmx-muted" /><input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="seu@email.com" className="input-mmx pl-10" required /></div>
              <div className="relative"><Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-mmx-muted" /><input type={showPwd ? 'text' : 'password'} value={password} onChange={e => setPassword(e.target.value)} placeholder="Senha" className="input-mmx pl-10 pr-10" required minLength={6} /><button type="button" onClick={() => setShowPwd(!showPwd)} className="absolute right-3 top-1/2 -translate-y-1/2 text-mmx-muted">{showPwd ? <EyeOff size={16} /> : <Eye size={16} />}</button></div>
              <button type="submit" disabled={loading} className="btn-primary w-full flex items-center justify-center gap-2">{loading ? <div className="w-5 h-5 rounded-full border-2 border-mmx-bg/30 border-t-mmx-bg animate-spin" /> : <>{mode === 'login' ? 'Entrar' : 'Criar Conta'} <ArrowRight size={18} /></>}</button>
            </form>
          </div>
          <p className="text-center text-xs text-mmx-muted mt-6">MMX Mechanics v1.0.0 - Figsmor Engenharia</p>
        </div>
      </div>
    </div>
  );
}