import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Search, Bell, Globe } from 'lucide-react';
export default function TopBar() {
  const { i18n } = useTranslation();
  const [lang, setLang] = useState(i18n.language);
  return (
    <header className="sticky top-0 z-40 glass border-b border-mmx-border">
      <div className="flex items-center justify-between px-6 py-3">
        <div className="relative w-full max-w-xl">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-mmx-muted" />
          <input type="text" placeholder="Buscar..." className="input-mmx pl-10 text-sm" />
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => { const n = lang === 'pt-BR' ? 'en' : 'pt-BR'; i18n.changeLanguage(n); setLang(n); }} className="p-2 rounded-xl hover:bg-mmx-elevated text-mmx-muted hover:text-mmx-text"><Globe size={18} /></button>
          <button className="relative p-2 rounded-xl hover:bg-mmx-elevated text-mmx-muted"><Bell size={18} /><span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-mmx-accent" /></button>
        </div>
      </div>
    </header>
  );
}