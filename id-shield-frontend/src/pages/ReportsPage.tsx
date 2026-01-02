import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  FileText, 
  Download,
  CheckCircle,
  Clock,
  XCircle,
  Filter
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { api } from '../lib/api';
import { useAuth } from '../lib/auth-context';
import { useDemo } from '../lib/demo-context';
import type { Case, Report } from '../types';

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'completed':
      return <CheckCircle className="w-4 h-4 text-green-400" />;
    case 'generating':
      return <Clock className="w-4 h-4 text-yellow-400" />;
    case 'failed':
      return <XCircle className="w-4 h-4 text-red-400" />;
    default:
      return <Clock className="w-4 h-4 text-muted-foreground" />;
  }
};

export function ReportsPage() {
  const { isDemoMode } = useAuth();
  const { demoCases, demoReports, showReadOnlyWarning } = useDemo();
  const [allReports, setAllReports] = useState<{ report: Report; caseData: Case }[]>([]);
  const [isLoading, setIsLoading] = useState(!isDemoMode);
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  useEffect(() => {
    if (isDemoMode) {
      const demoReportsWithCases = demoReports.map(r => ({
        report: r,
        caseData: demoCases.find(c => c.id === r.case_id) || demoCases[0]
      }));
      setAllReports(demoReportsWithCases);
      return;
    }
    
    const loadData = async () => {
      try {
        const casesRes = await api.getCases(1, 100);
        
        const reportPromises = casesRes.cases.map(async (c) => {
          const reports = await api.getCaseReports(c.id);
          return reports.map(r => ({ report: r, caseData: c }));
        });
        
        const reportArrays = await Promise.all(reportPromises);
        setAllReports(reportArrays.flat());
      } catch (err) {
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };
    
    loadData();
  }, [isDemoMode, demoCases, demoReports]);

  const filteredReports = allReports.filter(({ report }) => {
    if (typeFilter !== 'all' && report.report_type !== typeFilter) return false;
    if (statusFilter !== 'all' && report.status !== statusFilter) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Forensic Reports</h1>
        <p className="text-muted-foreground">
          Court-ready forensic analysis reports
        </p>
      </div>

      <Card className="bg-card border-border">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>All Reports</CardTitle>
              <CardDescription>{filteredReports.length} reports</CardDescription>
            </div>
            <div className="flex items-center gap-3">
              <Select value={typeFilter} onValueChange={setTypeFilter}>
                <SelectTrigger className="w-44 bg-input border-border">
                  <Filter className="w-4 h-4 mr-2" />
                  <SelectValue placeholder="Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="full_forensic">Full Forensic</SelectItem>
                  <SelectItem value="executive_summary">Executive Summary</SelectItem>
                  <SelectItem value="judge_summary">Judge Summary</SelectItem>
                  <SelectItem value="chain_of_custody">Chain of Custody</SelectItem>
                </SelectContent>
              </Select>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-36 bg-input border-border">
                  <Filter className="w-4 h-4 mr-2" />
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="generating">Generating</SelectItem>
                  <SelectItem value="completed">Completed</SelectItem>
                  <SelectItem value="failed">Failed</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="h-20 bg-muted/50 rounded-lg animate-pulse" />
              ))}
            </div>
          ) : filteredReports.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-medium text-foreground mb-2">No reports found</h3>
              <p className="text-muted-foreground">
                {typeFilter !== 'all' || statusFilter !== 'all'
                  ? 'Try adjusting your filters'
                  : 'Generate reports from case analysis to see them here'}
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredReports.map(({ report, caseData }) => (
                <div
                  key={report.id}
                  className="p-4 rounded-lg bg-muted/30 border border-border"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4">
                      <div className="w-10 h-10 rounded-lg bg-primary/20 flex items-center justify-center flex-shrink-0">
                        <FileText className="w-5 h-5 text-primary" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="font-medium text-foreground">
                            {report.title}
                          </h4>
                          {getStatusIcon(report.status)}
                        </div>
                        <p className="text-sm text-muted-foreground mb-1">
                          {report.report_number}
                        </p>
                        <div className="flex items-center gap-3 text-xs text-muted-foreground">
                          <Link 
                            to={`/cases/${caseData.id}`}
                            className="hover:text-primary transition-colors"
                          >
                            Case: {caseData.case_number}
                          </Link>
                          <span>•</span>
                          <span className="capitalize">{report.report_type.replace(/_/g, ' ')}</span>
                          <span>•</span>
                          <span>{new Date(report.created_at).toLocaleDateString()}</span>
                        </div>
                        {report.is_certified && (
                          <div className="mt-2">
                            <Badge className="bg-green-500/20 text-green-400 border-green-500/50">
                              <CheckCircle className="w-3 h-3 mr-1" />
                              Certified
                            </Badge>
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge className={
                        report.status === 'completed' 
                          ? 'bg-green-500/20 text-green-400' 
                          : report.status === 'failed'
                          ? 'bg-red-500/20 text-red-400'
                          : 'bg-yellow-500/20 text-yellow-400'
                      }>
                        {report.status}
                      </Badge>
                      {report.status === 'completed' && (
                        isDemoMode ? (
                          <Button size="sm" variant="outline" onClick={showReadOnlyWarning} className="opacity-60">
                            <Download className="w-4 h-4 mr-2" />
                            Download (Demo)
                          </Button>
                        ) : (
                          <a
                            href={api.getReportDownloadUrl(report.id)}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            <Button size="sm" variant="outline">
                              <Download className="w-4 h-4 mr-2" />
                              Download
                            </Button>
                          </a>
                        )
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <div className="p-4 rounded-lg bg-muted/50 border border-border">
        <p className="text-xs text-muted-foreground">
          All forensic reports are court-ready documents containing case information, evidence analysis, 
          confidence tiers, limitations, and chain-of-custody records. Reports are cryptographically 
          signed and certified for legal proceedings.
        </p>
      </div>
    </div>
  );
}
