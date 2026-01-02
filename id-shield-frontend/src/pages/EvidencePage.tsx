import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  FileSearch, 
  Image,
  Video,
  Music,
  File,
  Hash,
  AlertTriangle,
  CheckCircle,
  Clock,
  Filter
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { api } from '../lib/api';
import { useAuth } from '../lib/auth-context';
import { useDemo } from '../lib/demo-context';
import type { Case, Evidence } from '../types';

const getEvidenceIcon = (type: string) => {
  switch (type) {
    case 'photo':
    case 'screenshot':
      return Image;
    case 'video':
      return Video;
    case 'audio':
      return Music;
    default:
      return File;
  }
};

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'analyzed':
      return <CheckCircle className="w-4 h-4 text-green-400" />;
    case 'processing':
      return <Clock className="w-4 h-4 text-yellow-400" />;
    case 'failed':
    case 'quarantined':
      return <AlertTriangle className="w-4 h-4 text-red-400" />;
    default:
      return <Clock className="w-4 h-4 text-muted-foreground" />;
  }
};

export function EvidencePage() {
  const { isDemoMode } = useAuth();
  const { demoCases, demoEvidence } = useDemo();
  const [allEvidence, setAllEvidence] = useState<{ evidence: Evidence; caseData: Case }[]>([]);
  const [isLoading, setIsLoading] = useState(!isDemoMode);
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  useEffect(() => {
    if (isDemoMode) {
      const demoEvidenceWithCases = demoEvidence.map(e => ({
        evidence: e,
        caseData: demoCases.find(c => c.id === e.case_id) || demoCases[0]
      }));
      setAllEvidence(demoEvidenceWithCases);
      return;
    }
    
    const loadData = async () => {
      try {
        const casesRes = await api.getCases(1, 100);
        
        const evidencePromises = casesRes.cases.map(async (c) => {
          const evidenceRes = await api.getEvidence(c.id);
          return evidenceRes.evidence.map(e => ({ evidence: e, caseData: c }));
        });
        
        const evidenceArrays = await Promise.all(evidencePromises);
        setAllEvidence(evidenceArrays.flat());
      } catch (err) {
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };
    
    loadData();
  }, [isDemoMode, demoCases, demoEvidence]);

  const filteredEvidence = allEvidence.filter(({ evidence }) => {
    if (typeFilter !== 'all' && evidence.evidence_type !== typeFilter) return false;
    if (statusFilter !== 'all' && evidence.status !== statusFilter) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Evidence Repository</h1>
        <p className="text-muted-foreground">
          Browse all evidence across cases
        </p>
      </div>

      <Card className="bg-card border-border">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>All Evidence</CardTitle>
              <CardDescription>{filteredEvidence.length} items</CardDescription>
            </div>
            <div className="flex items-center gap-3">
              <Select value={typeFilter} onValueChange={setTypeFilter}>
                <SelectTrigger className="w-36 bg-input border-border">
                  <Filter className="w-4 h-4 mr-2" />
                  <SelectValue placeholder="Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="photo">Photos</SelectItem>
                  <SelectItem value="video">Videos</SelectItem>
                  <SelectItem value="audio">Audio</SelectItem>
                  <SelectItem value="screenshot">Screenshots</SelectItem>
                  <SelectItem value="document">Documents</SelectItem>
                </SelectContent>
              </Select>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-36 bg-input border-border">
                  <Filter className="w-4 h-4 mr-2" />
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="uploaded">Uploaded</SelectItem>
                  <SelectItem value="processing">Processing</SelectItem>
                  <SelectItem value="analyzed">Analyzed</SelectItem>
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
          ) : filteredEvidence.length === 0 ? (
            <div className="text-center py-12">
              <FileSearch className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-medium text-foreground mb-2">No evidence found</h3>
              <p className="text-muted-foreground">
                {typeFilter !== 'all' || statusFilter !== 'all'
                  ? 'Try adjusting your filters'
                  : 'Upload evidence to cases to see them here'}
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredEvidence.map(({ evidence, caseData }) => {
                const Icon = getEvidenceIcon(evidence.evidence_type);
                
                return (
                  <Link
                    key={evidence.id}
                    to={`/cases/${caseData.id}`}
                    className="block p-4 rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors border border-transparent hover:border-border"
                  >
                    <div className="flex items-start gap-4">
                      <div className="w-10 h-10 rounded-lg bg-primary/20 flex items-center justify-center flex-shrink-0">
                        <Icon className="w-5 h-5 text-primary" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="font-medium text-foreground truncate">
                            {evidence.original_filename}
                          </h4>
                          {getStatusIcon(evidence.status)}
                          <Badge variant="outline" className="capitalize">
                            {evidence.evidence_type}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground mb-1">
                          {evidence.evidence_number} • Case: {caseData.case_number}
                        </p>
                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                          <span>{(evidence.file_size / 1024 / 1024).toFixed(2)} MB</span>
                          <span className="flex items-center gap-1">
                            <Hash className="w-3 h-3" />
                            {evidence.sha256_hash.substring(0, 12)}...
                          </span>
                          {evidence.quality_score !== null && (
                            <span>Quality: {evidence.quality_score}/100</span>
                          )}
                        </div>
                      </div>
                      <Badge className={`status-${evidence.status}`}>
                        {evidence.status}
                      </Badge>
                    </div>
                  </Link>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
