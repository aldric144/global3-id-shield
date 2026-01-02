import { Link, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  FolderOpen, 
  FileSearch, 
  FileText, 
  Settings,
  Scale
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { useAuth } from '../../lib/auth-context';

const navItems = [
  { icon: LayoutDashboard, label: 'Dashboard', path: '/' },
  { icon: FolderOpen, label: 'Cases', path: '/cases' },
  { icon: FileSearch, label: 'Evidence', path: '/evidence' },
  { icon: FileText, label: 'Reports', path: '/reports' },
];

const adminItems = [
  { icon: Settings, label: 'Settings', path: '/settings' },
];

export function Sidebar() {
  const location = useLocation();
  const { user } = useAuth();

  const isActive = (path: string) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  };

  return (
    <aside className="w-64 h-[calc(100vh-4rem)] fixed left-0 top-16 bg-sidebar border-r border-sidebar-border">
      <nav className="p-4 space-y-2">
        <div className="mb-6">
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-3 mb-2">
            Main Menu
          </p>
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                isActive(item.path)
                  ? 'bg-sidebar-primary text-sidebar-primary-foreground'
                  : 'text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground'
              )}
            >
              <item.icon className="w-5 h-5" />
              {item.label}
            </Link>
          ))}
        </div>

        {user?.role === 'admin' && (
          <div>
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-3 mb-2">
              Administration
            </p>
            {adminItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                  isActive(item.path)
                    ? 'bg-sidebar-primary text-sidebar-primary-foreground'
                    : 'text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground'
                )}
              >
                <item.icon className="w-5 h-5" />
                {item.label}
              </Link>
            ))}
          </div>
        )}

        {user?.role === 'judge' && (
          <div className="mt-6 p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
            <div className="flex items-center gap-2 text-yellow-400">
              <Scale className="w-4 h-4" />
              <span className="text-xs font-medium">Read-Only Access</span>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Judicial review mode - evidence modification disabled
            </p>
          </div>
        )}
      </nav>

      <div className="absolute bottom-4 left-4 right-4">
        <div className="p-3 rounded-lg bg-card border border-border">
          <p className="text-xs text-muted-foreground">System Version</p>
          <p className="text-sm font-medium text-foreground">1.0.0-MVP</p>
          <p className="text-xs text-muted-foreground mt-1">Phase 1 Demo Environment</p>
        </div>
      </div>
    </aside>
  );
}
