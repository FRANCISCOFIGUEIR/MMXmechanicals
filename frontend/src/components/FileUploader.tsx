import { useState, useRef } from 'react';
import { UploadCloud, FileBox, CheckCircle2, Loader2, AlertCircle } from 'lucide-react';
import { FileAPI } from '../services/api';
export default function FileUploader({ onVoxelize }) {
  const [dragging, setDragging] = useState(false); const [uploading, setUploading] = useState(false); const [voxelizing, setVoxelizing] = useState(false);
  const [fileInfo, setFileInfo] = useState(null); const [gridSize, setGridSize] = useState(64); const [error, setError] = useState('');
  const inputRef = useRef(null);
  const handleFile = async (file) => { setUploading(true); setError(''); try { const { data } = await FileAPI.upload(file); setFileInfo(data); } catch (err) { setError('Erro ao enviar'); } finally { setUploading(false); } };
  const handleDrop = (e) => { e.preventDefault(); setDragging(false); const file = e.dataTransfer.files[0]; if (file) handleFile(file); };
  const handleVoxelize = async () => { if (!fileInfo) return; setVoxelizing(true); try { const { data } = await FileAPI.voxelize(fileInfo.filepath, gridSize, gridSize, gridSize, fileInfo.dimension); onVoxelize(data.grid_path); } catch (err) { setError('Erro na voxelizacao'); } finally { setVoxelizing(false); } };
  return (
    <div className="space-y-4">
      <div onDragOver={e => { e.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={handleDrop} onClick={() => inputRef.current?.click()} className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer ${dragging ? 'border-mmx-accent bg-mmx-accent/5' : 'border-mmx-border hover:border-mmx-accent/40'}`}>
        <input ref={inputRef} type="file" accept=".stl,.obj,.step,.stp,.iges,.igs,.dxf" onChange={e => e.target.files?.[0] && handleFile(e.target.files[0])} className="hidden" />
        {uploading ? <Loader2 size={32} className="text-mmx-accent animate-spin mx-auto" /> : <UploadCloud size={32} className="text-mmx-accent mx-auto" />}
        <p className="text-sm font-medium mt-3">Arraste e solte o arquivo aqui</p>
      </div>
      {error && <div className="flex items-center gap-2 p-3 rounded-xl bg-mmx-danger/10 text-mmx-danger text-sm"><AlertCircle size={16} /> {error}</div>}
      {fileInfo && <div className="card">
        <div className="flex items-center gap-3 mb-4"><CheckCircle2 size={20} className="text-mmx-accent" /><span className="text-sm font-semibold">Arquivo importado</span></div>
        <div className="grid grid-cols-2 gap-3 mb-4"><div className="p-2 rounded-lg bg-mmx-elevated"><p className="text-xs text-mmx-muted">Arquivo</p><p className="text-sm font-mono truncate">{fileInfo.filename}</p></div><div className="p-2 rounded-lg bg-mmx-elevated"><p className="text-xs text-mmx-muted">Formato</p><p className="text-sm font-mono">{fileInfo.format} - {fileInfo.dimension}</p></div></div>
        <div className="mb-4"><div className="flex justify-between mb-1.5"><label className="text-xs text-mmx-muted">Grade</label><span className="text-xs font-mono text-mmx-accent">{gridSize}^3</span></div><input type="range" min={16} max={128} step={8} value={gridSize} onChange={e => setGridSize(parseInt(e.target.value))} className="w-full accent-mmx-accent" /></div>
        <button onClick={handleVoxelize} disabled={voxelizing} className="btn-primary w-full flex items-center justify-center gap-2">{voxelizing ? <Loader2 size={18} className="animate-spin" /> : <FileBox size={18} />} Voxelizar</button>
      </div>}
    </div>
  );
}