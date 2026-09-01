import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Check, ChevronRight, ChevronLeft, Play, Thermometer, Grid3x3, Gauge } from 'lucide-react';
import { SimulationAPI, GeometryAPI } from '../services/api';
export default function SimulationNew() {
  const { t } = useTranslation(); const navigate = useNavigate(); const [params] = useSearchParams();
  const [step, setStep] = useState(0); const [loading, setLoading] = useState(false);
  const [config, setConfig] = useState({ name: `Sim_${Date.now().toString(36).slice(-6)}`, grid_size: 64, viscosity: 0.02, density: 1.0, inlet_velocity: 0.1, max_iterations: 10000, turbulence_model: 'les', enable_thermal: false, thermal_diffusivity: 0.05, T_inlet: 1.0, T_wall: 0.0, boundary_conditions: [{ face: 'west', type: 'velocity', params: { ux: 0.1, uy: 0, uz: 0 } }, { face: 'east', type: 'outflow' }, { face: 'south', type: 'wall' }, { face: 'north', type: 'wall' }] });
  const reynolds = (config.inlet_velocity * config.grid_size) / config.viscosity;
  const handleRun = async () => {
    setLoading(true);
    try {
      let gridPath = null; const geoId = params.get('geo');
      if (geoId) { const { data } = await GeometryAPI.generate(geoId, config.grid_size); gridPath = data.grid_path; }
      const { data } = await SimulationAPI.create({ project_id: 'default', name: config.name, grid_x: config.grid_size, grid_y: config.grid_size, grid_z: config.grid_size, viscosity: config.viscosity, density: config.density, inlet_velocity: config.inlet_velocity, max_iterations: config.max_iterations, turbulence_model: config.turbulence_model, enable_thermal: config.enable_thermal, thermal_diffusivity: config.thermal_diffusivity, T_inlet: config.T_inlet, T_wall: config.T_wall, boundary_conditions: config.boundary_conditions, grid_path: gridPath, async: false });
      navigate(`/simulation/${data.simulation_id}`);
    } catch (err) { console.error(err); } finally { setLoading(false); }
  };
  const steps = ['Geometria', 'Fisica', 'Condicoes', 'Revisao'];
  return (
    <div className="space-y-6">
      <h1 className="font-display text-2xl font-bold">{t('simulation.new')}</h1>
      <div className="flex items-center gap-2">
        {steps.map((s, i) => <div key={i} className="flex items-center flex-1">
          <div className={`flex items-center gap-2 ${i <= step ? 'text-mmx-accent' : 'text-mmx-muted'}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${i < step ? 'bg-mmx-accent text-mmx-bg' : i === step ? 'bg-mmx-accent/20 border-2 border-mmx-accent' : 'bg-mmx-surface border border-mmx-border'}`}>{i < step ? <Check size={14} /> : i + 1}</div>
            <span className="text-sm font-medium hidden sm:block">{s}</span>
          </div>
          {i < steps.length - 1 && <div className={`flex-1 h-px mx-2 ${i < step ? 'bg-mmx-accent' : 'bg-mmx-border'}`} />}
        </div>)}
      </div>
      <div className="card max-w-2xl">
        {step === 0 && <div className="space-y-4">
          <h2 className="section-title">Geometria</h2>
          <input type="text" value={config.name} onChange={e => setConfig({ ...config, name: e.target.value })} className="input-mmx" />
          <div><div className="flex justify-between mb-1.5"><label className="text-xs text-mmx-muted">Grade</label><span className="text-xs font-mono text-mmx-accent">{config.grid_size}^3</span></div><input type="range" min={16} max={128} step={8} value={config.grid_size} onChange={e => setConfig({ ...config, grid_size: parseInt(e.target.value) })} className="w-full accent-mmx-accent" /></div>
          <div className="p-3 rounded-xl bg-mmx-elevated flex items-center gap-3"><Grid3x3 size={18} className="text-mmx-accent-2" /><div><p className="text-xs text-mmx-muted">Celulas</p><p className="text-sm font-mono">{(config.grid_size ** 3).toLocaleString()}</p></div></div>
        </div>}
        {step === 1 && <div className="space-y-4">
          <h2 className="section-title">Fisica</h2>
          <div><div className="flex justify-between mb-1.5"><label className="text-xs text-mmx-muted">Densidade</label><span className="text-xs font-mono text-mmx-accent">{config.density}</span></div><input type="range" min={0.1} max={10} step={0.1} value={config.density} onChange={e => setConfig({ ...config, density: parseFloat(e.target.value) })} className="w-full accent-mmx-accent" /></div>
          <div><div className="flex justify-between mb-1.5"><label className="text-xs text-mmx-muted">Viscosidade</label><span className="text-xs font-mono text-mmx-accent">{config.viscosity}</span></div><input type="range" min={0.001} max={0.1} step={0.001} value={config.viscosity} onChange={e => setConfig({ ...config, viscosity: parseFloat(e.target.value) })} className="w-full accent-mmx-accent" /></div>
          <div><div className="flex justify-between mb-1.5"><label className="text-xs text-mmx-muted">Velocidade</label><span className="text-xs font-mono text-mmx-accent">{config.inlet_velocity}</span></div><input type="range" min={0.01} max={0.5} step={0.01} value={config.inlet_velocity} onChange={e => setConfig({ ...config, inlet_velocity: parseFloat(e.target.value) })} className="w-full accent-mmx-accent" /></div>
          <div className="flex gap-2">{['none','les'].map(m => <button key={m} onClick={() => setConfig({ ...config, turbulence_model: m })} className={`flex-1 py-2 rounded-lg text-xs font-medium ${config.turbulence_model === m ? 'bg-mmx-accent text-mmx-bg' : 'glass text-mmx-muted'}`}>{m === 'none' ? 'Laminar' : 'LES'}</button>)}</div>
          <div className="p-3 rounded-xl bg-mmx-elevated flex items-center gap-3"><Gauge size={18} className="text-mmx-accent-3" /><div><p className="text-xs text-mmx-muted">Reynolds</p><p className="text-sm font-mono text-mmx-accent-3">Re = {reynolds.toFixed(0)}</p></div></div>
          <button onClick={() => setConfig({ ...config, enable_thermal: !config.enable_thermal })} className="w-full flex items-center justify-between p-3 rounded-xl bg-mmx-surface border border-mmx-border"><div className="flex items-center gap-3"><Thermometer size={18} className={config.enable_thermal ? 'text-mmx-danger' : 'text-mmx-muted'} /><span className="text-sm">Analise Termica</span></div><div className={`w-10 h-6 rounded-full ${config.enable_thermal ? 'bg-mmx-accent' : 'bg-mmx-border'}`}><div className={`w-4 h-4 rounded-full bg-mmx-bg transition-transform ${config.enable_thermal ? 'translate-x-5' : 'translate-x-1'}`} /></div></button>
        </div>}
        {step === 2 && <div className="space-y-4"><h2 className="section-title">Condicoes de Contorno</h2>{config.boundary_conditions.map((bc, i) => <div key={i} className="flex items-center justify-between p-3 rounded-xl bg-mmx-elevated"><span className="badge badge-queued">{bc.face}</span><span className="text-sm">{bc.type}</span></div>)}</div>}
        {step === 3 && <div className="space-y-4"><h2 className="section-title">Revisao</h2><div className="grid grid-cols-2 gap-3">{[["Nome", config.name], ["Grade", `${config.grid_size}^3`], ["Reynolds", reynolds.toFixed(0)], ["Iteracoes", config.max_iterations], ["Turbulencia", config.turbulence_model], ["Termico", config.enable_thermal ? 'Sim' : 'Nao']].map((r, i) => <div key={i} className="p-3 rounded-xl bg-mmx-elevated"><p className="text-xs text-mmx-muted">{r[0]}</p><p className="text-sm font-mono">{r[1]}</p></div>)}</div></div>}
      </div>
      <div className="flex justify-between max-w-2xl">
        <button onClick={() => setStep(Math.max(0, step - 1))} disabled={step === 0} className="btn-ghost flex items-center gap-2 text-sm disabled:opacity-30"><ChevronLeft size={16} /> Voltar</button>
        {step < 3 ? <button onClick={() => setStep(step + 1)} className="btn-primary flex items-center gap-2 text-sm">Proximo <ChevronRight size={16} /></button> : <button onClick={handleRun} disabled={loading} className="btn-primary flex items-center gap-2 text-sm">{loading ? <div className="w-4 h-4 rounded-full border-2 border-mmx-bg/30 border-t-mmx-bg animate-spin" /> : <Play size={16} />} Executar</button>}
      </div>
    </div>
  );
}