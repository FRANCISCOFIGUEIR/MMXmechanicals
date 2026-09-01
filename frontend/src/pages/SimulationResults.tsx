import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Download, CheckCircle2, XCircle, Clock, Cpu, Activity } from 'lucide-react';
import { SimulationAPI } from '../services/api';
import Viewer3D from '../components/Viewer3D';
export default function SimulationResults() {
  const { id } = useParams(); const navigate = useNavigate();
  const [sim, setSim] = useState(null); const [results, setResults] = useState(null); const [loading, setLoading] = useState(true); const [field, setField] = useState('velocity');
  useEffect(() => {
    if (!id) return;
    const poll = async () => {
      try {
        const { data } = await SimulationAPI.get(id); setSim(data);
        if (data.status === 'completed') { const { data: res } = await SimulationAPI.getResults(id); setResults(res); setLoading(false); }
        else if (data.status === 'failed') setLoading(false);
        else setTimeout(poll, 2000);
      } catch { setLoading(false); }
    }; poll();
  }, [id]);
  if (loading && !sim) return <div className="flex items-center justify-center h-96"><div className="w-12 h-12 rounded-full border-4 border-mmx-border border-t-mmx-accent animate-spin" /></div>;
  if (!sim) return <div className="text-mmx-muted">Nao encontrada</div>;
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <button onClick={() => navigate('/')} className="p-2 rounded-xl hover:bg-mmx-elevated"><ArrowLeft size={18} className="text-mmx-muted" /></button>
        <div><h1 className="font-display text-xl font-bold">{sim.name}</h1><p className="text-xs text-mmx-muted">{sim.grid_size} - {sim.gpu_used ? 'GPU' : 'CPU'}</p></div>
      </div>
      {sim.status === 'completed' && results && <>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[{ icon: CheckCircle2, label: 'Convergiu', value: results.converged ? 'Sim' : 'Nao', color: 'text-mmx-accent' },
            { icon: Clock, label: 'Tempo', value: `${results.compute_time?.toFixed(1)}s`, color: 'text-mmx-accent-2' },
            { icon: Cpu, label: 'GPU', value: results.gpu_used ? 'CUDA' : 'CPU', color: 'text-mmx-accent-3' },
            { icon: Activity, label: 'Iteracoes', value: results.total_iterations?.toLocaleString(), color: 'text-mmx-warn' }].map((s, i) => (
            <div key={i} className="card flex items-center gap-3"><s.icon size={20} className={s.color} /><div><p className="text-xs text-mmx-muted">{s.label}</p><p className="text-sm font-mono">{s.value}</p></div></div>))}
        </div>
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="section-title">Resultados</h2>
            <div className="flex gap-2">{['velocity','pressure','temperature'].map(f => <button key={f} onClick={() => setField(f)} className={`px-3 py-1.5 rounded-lg text-xs font-medium ${field === f ? 'bg-mmx-accent text-mmx-bg' : 'glass text-mmx-muted'}`}>{f}</button>)}</div>
          </div>
          <Viewer3D field={field} simId={id} />
        </div>
      </>}
      {sim.status === 'failed' && <div className="card flex items-center gap-4"><XCircle size={24} className="text-mmx-danger" /><div><p className="font-semibold text-mmx-danger">Falhou</p><p className="text-sm text-mmx-muted">{sim.error_message}</p></div></div>}
    </div>
  );
}