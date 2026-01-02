import { useState } from 'react';
import { Shield, AlertCircle } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Alert, AlertDescription } from '../components/ui/alert';
import { useAuth } from '../lib/auth-context';

export function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await login(email, password);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-20 h-20 rounded-2xl bg-primary/20 flex items-center justify-center mx-auto mb-4">
            <Shield className="w-12 h-12 text-primary" />
          </div>
          <h1 className="text-3xl font-bold text-foreground">ID SHIELD™</h1>
          <p className="text-muted-foreground mt-2">Global3 Technology & Intelligence</p>
          <p className="text-sm text-muted-foreground">Forensic Intelligence Platform</p>
        </div>

        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle>Secure Access</CardTitle>
            <CardDescription>
              Enter your credentials to access the forensic analysis platform
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <div className="space-y-2">
                <Label htmlFor="email">Email Address</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="agent@agency.gov"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="bg-input border-border"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="bg-input border-border"
                />
              </div>

              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? 'Authenticating...' : 'Access Platform'}
              </Button>
            </form>

            <div className="mt-6 p-4 rounded-lg bg-muted/50 border border-border">
              <p className="text-xs text-muted-foreground text-center">
                This is a secure government forensic system. Unauthorized access is prohibited and monitored.
                All actions are logged for chain-of-custody compliance.
              </p>
            </div>

            <div className="mt-4 p-3 rounded-lg bg-blue-500/10 border border-blue-500/20">
              <p className="text-xs text-blue-400 font-medium">Demo Credentials:</p>
              <p className="text-xs text-muted-foreground mt-1">
                Admin: admin@global3ti.com / admin123<br />
                Investigator: investigator@global3ti.com / investigator123<br />
                Judge: judge@global3ti.com / judge123
              </p>
            </div>
          </CardContent>
        </Card>

        <p className="text-center text-xs text-muted-foreground mt-6">
          Phase 1 MVP Demo Environment • v1.0.0
        </p>
      </div>
    </div>
  );
}
