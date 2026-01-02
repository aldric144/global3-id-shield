import { Shield, LogOut, User } from 'lucide-react';
import { Button } from '../ui/button';
import { useAuth } from '../../lib/auth-context';

export function Header() {
  const { user, logout } = useAuth();

  return (
    <header className="h-16 border-b border-border bg-card/50 backdrop-blur-sm fixed top-0 left-0 right-0 z-50">
      <div className="h-full px-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-primary/20 flex items-center justify-center">
            <Shield className="w-6 h-6 text-primary" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-foreground">ID SHIELD™</h1>
            <p className="text-xs text-muted-foreground">Global3 Technology & Intelligence</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-sm font-medium text-foreground">
              {user?.first_name} {user?.last_name}
            </p>
            <p className="text-xs text-muted-foreground capitalize">
              {user?.role} {user?.badge_number && `• ${user.badge_number}`}
            </p>
          </div>
          <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
            <User className="w-5 h-5 text-primary" />
          </div>
          <Button variant="ghost" size="icon" onClick={logout} title="Logout">
            <LogOut className="w-5 h-5" />
          </Button>
        </div>
      </div>
    </header>
  );
}
