import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Circle, Square, Box, Layers, Wind, Thermometer, ArrowRight } from 'lucide-react';
const GEOS = [
  { id: 'cylinder-flow', name: 'Escoamento sobre Cilindro', dim: '2D', cat: 'Externos', diff: 'Iniciante', re: 100, icon: Circle },
  { id: 'channel-flow', name: 'Canal Plano 2D', dim: '2D', cat: 'Internos', diff: 'Iniciante', re: 50, icon: Square },
  { id: 'lid-cavity', name: 'Cavidade com Tampa', dim: '2D', cat: 'Validacao', diff: 'Iniciante', re: 400, icon: Box },
  { id: 'backward-step', name: 'Degrau Atras', dim: '2D', cat: 'Internos', diff: 'Intermediario', re: 500, icon: Layers },
  { id: 'sphere-3d', name: 'Esfera em 3D', dim: '3D', cat: 'Externos', diff: 'Intermediario', re: 200, icon: Circle },
  { id: '3d-duct', name: 'Duto Retangular 3D', dim: '3D', cat: 'Industriais', diff: 'Intermediario', re: 300, icon: Square },
  { id: 'heat-tube', name: 'Tubo com Troca Termica', dim: '3D', cat: 'Industriais', diff: 'Avancado', re: 150, icon: Thermometer },
];
export default function GeometryLibrary() {
  const navigate = useNavigate(); const [search, setSearch] = useState(''); const [dim, setDim] = useState('Todos');
  const filtered = GEOS.filter(g => (!search || g.name.toLowerCase().includes(search.toLowerCase())) && (dim === 'Todos' || g.dim === dim));
  return (
    <div className="space-y-6">
      <div><h1 className="font-display text-2xl font-bold">Biblioteca de Geometrias</h1><p className="text-mmx-muted text-sm mt-1">7 geometrias pre-configuradas</p></div>
      <div className="flex gap-3">
        <div className="relative flex-1"><Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-mmx-muted" /><input type="text" value={search} onChange={e => setSearch(e.target.value)} placeholder="Buscar..." className="input-mmx pl-10" /></div>
        <div className="flex gap-2">{['Todos','2D','3D'].map(d => <button key={d} onClick={() => setDim(d)} className={`px-4 py-2.5 rounded-xl text-sm font-medium ${dim === d ? 'bg-mmx-accent text-mmx-bg' : 'glass text-mmx-muted'}`}>{d}</button>)}</div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((g, i) => <div key={g.id} className="card group hover:border-mmx-accent/30 cursor-pointer animate-slide-up" style={{ animationDelay: `${i*30}ms` }} onClick={() => navigate(`/simulation/new?geo=${g.id}`)}>
          <div className="h-32 rounded-xl bg-mmx-bg mb-4 flex items-center justify-center"><g.icon size={40} className="text-mmx-accent group-hover:scale-110 transition-transform" /></div>
          <h3 className="font-semibold text-sm mb-2">{g.name}</h3>
          <div className="flex justify-between text-xs text-mmx-muted"><span>{g.dim} · {g.cat}</span><span className="font-mono">Re={g.re}</span></div>
          <ArrowRight size={14} className="text-mmx-accent mt-3 opacity-0 group-hover:opacity-100" />
        </div>)}
      </div>
    </div>
  );
}