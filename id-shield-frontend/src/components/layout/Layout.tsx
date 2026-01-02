import { ReactNode } from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { useAuth } from '../../lib/auth-context';
import { AlertTriangle } from 'lucide-react';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const { isDemoMode } = useAuth();

  return (
    <div className="min-h-screen bg-background">
      {isDemoMode && (
        <div className="fixed top-0 left-0 right-0 z-50 bg-amber-600 text-white px-4 py-2 text-center text-sm font-medium flex items-center justify-center gap-2">
          <AlertTriangle className="h-4 w-4" />
          <span>Phase 1 MVP - Demo / Read-Only Mode | Backend not connected | Write actions disabled</span>
          <AlertTriangle className="h-4 w-4" />
        </div>
      )}
      <Header />
      <Sidebar />
      <main className={`ml-64 min-h-screen ${isDemoMode ? 'pt-24' : 'pt-16'}`}>
        <div className="p-6">
          {children}
        </div>
      </main>
    </div>
  );
}
