import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  FolderOpen, 
  FileSearch, 
  AlertTriangle,
  CheckCircle,
  Clock,
  TrendingUp,
  Shield
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { api } from '../lib/api';
import { useAuth } from '../lib/auth-context';
import { useDemo } from '../lib/demo-context';
import type { Case } from '../types';

export function DashboardPage() {
  const { user, isDemoMode } = useAuth();
  const { demoCases, showReadOnlyWarning } = useDemo();
  const [cases, setCases] = useState<Case[]>([]);
  const [isLoading, setIsLoading] = useState(!isDemoMode);

  useEffect(() => {
    if (isDemoMode) {
      setCases(demoCases);
      return;
    }
    api.getCases(1, 5)
      .then((response) => setCases(response.cases))
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, [isDemoMode, demoCases]);

  const stats = {
    totalCases: cases.length,
    openCases: cases.filter(c => c.status === 'open' || c.status === 'in_progress').length,
    pendingReview: cases.filter(c => c.status === 'pending_review').length,
    totalEvidence: cases.reduce((sum, c) => sum + c.evidence_count, 0),
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Dashboard</h1>
          <p className="text-muted-foreground">
            Welcome back, {user?.first_name}. Here's your forensic analysis overview.
          </p>
        </div>
        {user?.role !== 'judge' && (
          isDemoMode ? (
            <Button onClick={showReadOnlyWarning} variant="outline" className="opacity-60">
              <FolderOpen className="w-4 h-4 mr-2" />
              New Case (Demo)
            </Button>
          ) : (
            <Link to="/cases/new">
              <Button>
                <FolderOpen className="w-4 h-4 mr-2" />
                New Case
              </Button>
            </Link>
          )
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-card border-border">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Cases</p>
                <p className="text-3xl font-bold text-foreground">{stats.totalCases}</p>
              </div>
              <div className="w-12 h-12 rounded-lg bg-primary/20 flex items-center justify-center">
                <FolderOpen className="w-6 h-6 text-primary" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Active Cases</p>
                <p className="text-3xl font-bold text-foreground">{stats.openCases}</p>
              </div>
              <div className="w-12 h-12 rounded-lg bg-green-500/20 flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-green-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Pending Review</p>
                <p className="text-3xl font-bold text-foreground">{stats.pendingReview}</p>
              </div>
              <div className="w-12 h-12 rounded-lg bg-yellow-500/20 flex items-center justify-center">
                <Clock className="w-6 h-6 text-yellow-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Evidence Items</p>
                <p className="text-3xl font-bold text-foreground">{stats.totalEvidence}</p>
              </div>
              <div className="w-12 h-12 rounded-lg bg-blue-500/20 flex items-center justify-center">
                <FileSearch className="w-6 h-6 text-blue-400" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FolderOpen className="w-5 h-5" />
              Recent Cases
            </CardTitle>
            <CardDescription>Latest cases in your agency</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-16 bg-muted/50 rounded-lg animate-pulse" />
                ))}
              </div>
            ) : cases.length === 0 ? (
              <div className="text-center py-8">
                <FolderOpen className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
                <p className="text-muted-foreground">No cases yet</p>
                {user?.role !== 'judge' && (
                  <Link to="/cases/new">
                    <Button variant="outline" className="mt-3">Create First Case</Button>
                  </Link>
                )}
              </div>
            ) : (
              <div className="space-y-3">
                {cases.map((caseItem) => (
                  <Link
                    key={caseItem.id}
                    to={`/cases/${caseItem.id}`}
                    className="block p-4 rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors border border-transparent hover:border-border"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-foreground">{caseItem.title}</p>
                        <p className="text-sm text-muted-foreground">{caseItem.case_number}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge className={`status-${caseItem.status}`}>
                          {caseItem.status.replace('_', ' ')}
                        </Badge>
                        <Badge className={`priority-${caseItem.priority}`}>
                          {caseItem.priority}
                        </Badge>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="w-5 h-5" />
              System Status
            </CardTitle>
            <CardDescription>Platform health and capabilities</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 rounded-lg bg-green-500/10 border border-green-500/20">
                <div className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span className="text-sm font-medium text-foreground">Analysis Engine</span>
                </div>
                <Badge className="bg-green-500/20 text-green-400">Operational</Badge>
              </div>

              <div className="flex items-center justify-between p-3 rounded-lg bg-green-500/10 border border-green-500/20">
                <div className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span className="text-sm font-medium text-foreground">Report Generator</span>
                </div>
                <Badge className="bg-green-500/20 text-green-400">Operational</Badge>
              </div>

              <div className="flex items-center justify-between p-3 rounded-lg bg-green-500/10 border border-green-500/20">
                <div className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span className="text-sm font-medium text-foreground">Chain of Custody</span>
                </div>
                <Badge className="bg-green-500/20 text-green-400">Active</Badge>
              </div>

              <div className="flex items-center justify-between p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
                <div className="flex items-center gap-3">
                  <AlertTriangle className="w-5 h-5 text-yellow-400" />
                  <span className="text-sm font-medium text-foreground">Advanced AI Models</span>
                </div>
                <Badge className="bg-yellow-500/20 text-yellow-400">MVP Mode</Badge>
              </div>
            </div>

            <div className="mt-4 p-3 rounded-lg bg-muted/50 border border-border">
              <p className="text-xs text-muted-foreground">
                Phase 1 MVP: Real forensic components (hashing, metadata, quality) with structured mock outputs for advanced AI analysis. All outputs are confidence-tiered and court-ready.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
