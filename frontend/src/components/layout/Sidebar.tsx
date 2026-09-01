import { NavLink, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { LayoutDashboard, FolderKanban, FlaskConical, Library, Settings, LogOut, Zap, ChevronRight } from 'lucide-react';
const navItems = [
  { key: 'dashboard', icon: LayoutDashboard, path: '/' },
  { key: 'projects', icon: FolderKanban, path: '/projects' },
  { key: 'simulations', icon: FlaskConical, path: '/simulations' },
  { key: 'library', icon: Library, path: '/library' },
  { key: 'settings', icon: Settings, path: '/settings' },
];
export default function Sidebar() {
  const { t } = useTranslation();
  const location = useLocation();
  return (
    <aside className="fixed left-0 top-0 h-screen w-[240px] glass-strong z-50 flex flex-col">
      <div className="px-6 py-6 border-b border-mmx-border">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-mmx-accent to-mmx-accent-2 flex items-center justify-center font-display font-bold text-mmx-bg text-lg">MX</div>
          <div><h1 className="font-display font-bold text-base">MMX <span className="gradient-text">Mechanics</span></h1>
          <p className="text-[10px] text-mmx-muted tracking-wider uppercase">CFD Engine</p></div>
        </div>
      </div>
      <nav className="flex-1 py-4 px-3 space-y-1">
        {navItems.map(item => {
          const active = location.pathname === item.path;
          return (
            <NavLink key={item.key} to={item.path} className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${active ? 'bg-mmx-accent/10 text-mmx-accent border border-mmx-accent/20' : 'text-mmx-muted hover:text-mmx-text hover:bg-mmx-elevated border border-transparent'}`}>
              <item.icon size={18} className={active ? 'text-mmx-accent' : 'text-mmx-muted'} />
              <span>{t(`nav.${item.key}`)}</span>
              {active && <ChevronRight size={14} className="ml-auto text-mmx-accent" />}
            </NavLink>
          );
        })}
      </nav>
      <div className="px-4 py-3 border-t border-mmx-border">
        <div className="glass rounded-xl p-3 flex items-center gap-3">
          <div className="w-2 h-2 rounded-full bg-mmx-accent animate-pulse" />
          <div className="flex-1"><p className="text-xs font-semibold">GPU Engine</p><p className="text-[10px] text-mmx-muted">CUDA CuPy D3Q19</p></div>
          <Zap size={16} className="text-mmx-accent" />
        </div>
      </div>
      <div className="px-4 py-4 border-t border-mmx-border flex items-center gap-3">
        <div className="w-9 h-9 rounded-full bg-gradient-to-br from-mmx-accent-3 to-mmx-accent-2 flex items-center justify-center text-mmx-bg font-bold text-sm">FF</div>
        <div className="flex-1 min-w-0"><p className="text-sm font-semibold truncate">Francisco</p><p className="text-[10px] text-mmx-muted truncate">Figsmor Engenharia</p></div>
        <button className="text-mmx-muted hover:text-mmx-danger"><LogOut size={16} /></button>
      </div>
    </aside>
  );
}