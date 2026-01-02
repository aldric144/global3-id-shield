import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  FolderOpen, 
  Plus, 
  Search,
  Filter,
  Calendar,
  MapPin
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { api } from '../lib/api';
import { useAuth } from '../lib/auth-context';
import { useDemo } from '../lib/demo-context';
import type { Case } from '../types';

export function CasesPage() {
  const { user, isDemoMode } = useAuth();
  const { demoCases, showReadOnlyWarning } = useDemo();
  const [cases, setCases] = useState<Case[]>([]);
  const [isLoading, setIsLoading] = useState(!isDemoMode);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);

  useEffect(() => {
    if (isDemoMode) {
      let filtered = demoCases;
      if (statusFilter !== 'all') {
        filtered = filtered.filter(c => c.status === statusFilter);
      }
      if (search) {
        const searchLower = search.toLowerCase();
        filtered = filtered.filter(c => 
          c.title.toLowerCase().includes(searchLower) || 
          c.case_number.toLowerCase().includes(searchLower)
        );
      }
      setCases(filtered);
      setTotal(filtered.length);
      return;
    }
    setIsLoading(true);
    api.getCases(page, 20, statusFilter === 'all' ? undefined : statusFilter, search || undefined)
      .then((response) => {
        setCases(response.cases);
        setTotal(response.total);
      })
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, [page, statusFilter, search, isDemoMode, demoCases]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Cases</h1>
          <p className="text-muted-foreground">
            Manage forensic investigation cases
          </p>
        </div>
        {user?.role !== 'judge' && (
          isDemoMode ? (
            <Button onClick={showReadOnlyWarning} variant="outline" className="opacity-60">
              <Plus className="w-4 h-4 mr-2" />
              New Case (Demo)
            </Button>
          ) : (
            <Link to="/cases/new">
              <Button>
                <Plus className="w-4 h-4 mr-2" />
                New Case
              </Button>
            </Link>
          )
        )}
      </div>

      <Card className="bg-card border-border">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Case Management</CardTitle>
              <CardDescription>{total} total cases</CardDescription>
            </div>
            <div className="flex items-center gap-3">
              <form onSubmit={handleSearch} className="flex items-center gap-2">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    placeholder="Search cases..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="pl-9 w-64 bg-input border-border"
                  />
                </div>
              </form>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-40 bg-input border-border">
                  <Filter className="w-4 h-4 mr-2" />
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="open">Open</SelectItem>
                  <SelectItem value="in_progress">In Progress</SelectItem>
                  <SelectItem value="pending_review">Pending Review</SelectItem>
                  <SelectItem value="closed">Closed</SelectItem>
                  <SelectItem value="archived">Archived</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="h-24 bg-muted/50 rounded-lg animate-pulse" />
              ))}
            </div>
          ) : cases.length === 0 ? (
            <div className="text-center py-12">
              <FolderOpen className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-medium text-foreground mb-2">No cases found</h3>
              <p className="text-muted-foreground mb-4">
                {search || statusFilter !== 'all' 
                  ? 'Try adjusting your search or filters'
                  : 'Create your first case to get started'}
              </p>
              {user?.role !== 'judge' && !search && statusFilter === 'all' && (
                <Link to="/cases/new">
                  <Button>
                    <Plus className="w-4 h-4 mr-2" />
                    Create First Case
                  </Button>
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
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="font-semibold text-foreground">{caseItem.title}</h3>
                        <Badge className={`status-${caseItem.status}`}>
                          {caseItem.status.replace('_', ' ')}
                        </Badge>
                        <Badge className={`priority-${caseItem.priority}`}>
                          {caseItem.priority}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground mb-2">
                        {caseItem.case_number} • {caseItem.case_type}
                      </p>
                      {caseItem.description && (
                        <p className="text-sm text-muted-foreground line-clamp-1">
                          {caseItem.description}
                        </p>
                      )}
                      <div className="flex items-center gap-4 mt-3 text-xs text-muted-foreground">
                        {caseItem.incident_date && (
                          <span className="flex items-center gap-1">
                            <Calendar className="w-3 h-3" />
                            {new Date(caseItem.incident_date).toLocaleDateString()}
                          </span>
                        )}
                        {caseItem.incident_location && (
                          <span className="flex items-center gap-1">
                            <MapPin className="w-3 h-3" />
                            {caseItem.incident_location}
                          </span>
                        )}
                        <span>{caseItem.evidence_count} evidence items</span>
                      </div>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}

          {total > 20 && (
            <div className="flex items-center justify-center gap-2 mt-6">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
              >
                Previous
              </Button>
              <span className="text-sm text-muted-foreground">
                Page {page} of {Math.ceil(total / 20)}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage(p => p + 1)}
                disabled={page >= Math.ceil(total / 20)}
              >
                Next
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
