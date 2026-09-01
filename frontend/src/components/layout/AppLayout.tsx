import { ReactNode } from 'react';
import Sidebar from './Sidebar';
import TopBar from './TopBar';
export default function AppLayout({ children }) {
  return (
    <div className="min-h-screen bg-mmx-bg text-mmx-text">
      <div className="fixed inset-0 grid-bg opacity-30 pointer-events-none" />
      <div className="fixed top-0 right-0 w-[600px] h-[600px] bg-mmx-accent/5 rounded-full blur-[120px] pointer-events-none" />
      <Sidebar />
      <div className="ml-[240px] min-h-screen flex flex-col relative z-10">
        <TopBar />
        <main className="flex-1 p-6 animate-fade-in">{children}</main>
      </div>
    </div>
  );
}