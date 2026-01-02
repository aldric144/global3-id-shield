import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  ArrowLeft, 
  Upload, 
  FileSearch, 
  FileText, 
  Play,
  Download,
  AlertTriangle,
  CheckCircle,
  Clock,
  XCircle,
  Image,
  Video,
  Music,
  File,
  Shield,
  Hash,
  Calendar,
  MapPin,
  Loader2
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Alert, AlertDescription } from '../components/ui/alert';
import { api } from '../lib/api';
import { useAuth } from '../lib/auth-context';
import { useDemo } from '../lib/demo-context';
import type { Case, Evidence, AnalysisResult, Report } from '../types';

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

const getConfidenceColor = (tier?: string) => {
  switch (tier) {
    case 'high':
      return 'text-green-400 bg-green-500/20 border-green-500/50';
    case 'moderate':
      return 'text-yellow-400 bg-yellow-500/20 border-yellow-500/50';
    case 'limited':
      return 'text-orange-400 bg-orange-500/20 border-orange-500/50';
    case 'insufficient':
      return 'text-red-400 bg-red-500/20 border-red-500/50';
    default:
      return 'text-muted-foreground bg-muted/20 border-muted';
  }
};

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'completed':
      return <CheckCircle className="w-4 h-4 text-green-400" />;
    case 'running':
    case 'pending':
      return <Clock className="w-4 h-4 text-yellow-400" />;
    case 'failed':
      return <XCircle className="w-4 h-4 text-red-400" />;
    case 'skipped':
      return <AlertTriangle className="w-4 h-4 text-orange-400" />;
    default:
      return <Clock className="w-4 h-4 text-muted-foreground" />;
  }
};

export function CaseDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user, isDemoMode } = useAuth();
  const { demoCases, demoEvidence, demoAnalysisResults, demoReports, showReadOnlyWarning } = useDemo();
  
  const [caseData, setCaseData] = useState<Case | null>(null);
  const [evidence, setEvidence] = useState<Evidence[]>([]);
  const [analysisResults, setAnalysisResults] = useState<AnalysisResult[]>([]);
  const [reports, setReports] = useState<Report[]>([]);
  const [isLoading, setIsLoading] = useState(!isDemoMode);
  const [selectedEvidence, setSelectedEvidence] = useState<Evidence | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState<number | null>(null);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [reportDialogOpen, setReportDialogOpen] = useState(false);
  const [error, setError] = useState('');

  const [uploadForm, setUploadForm] = useState({
    file: null as File | null,
    description: '',
    source: '',
    collector_name: ''
  });

  const [reportForm, setReportForm] = useState({
    title: '',
    report_type: 'full_forensic'
  });

  const loadData = useCallback(async () => {
    if (!id) return;
    
    if (isDemoMode) {
      const caseId = parseInt(id);
      const foundCase = demoCases.find(c => c.id === caseId) || demoCases[0];
      setCaseData(foundCase);
      setEvidence(demoEvidence.filter(e => e.case_id === foundCase.id));
      setAnalysisResults(demoAnalysisResults.filter(a => 
        demoEvidence.some(e => e.case_id === foundCase.id && e.id === a.evidence_id)
      ));
      setReports(demoReports.filter(r => r.case_id === foundCase.id));
      return;
    }
    
    try {
      const [caseRes, evidenceRes, analysisRes, reportsRes] = await Promise.all([
        api.getCase(parseInt(id)),
        api.getEvidence(parseInt(id)),
        api.getCaseAnalysis(parseInt(id)),
        api.getCaseReports(parseInt(id))
      ]);
      setCaseData(caseRes);
      setEvidence(evidenceRes.evidence);
      setAnalysisResults(analysisRes);
      setReports(reportsRes);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }, [id, isDemoMode, demoCases, demoEvidence, demoAnalysisResults, demoReports]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadForm.file || !id) return;
    
    setIsUploading(true);
    setError('');
    
    try {
      await api.uploadEvidence(parseInt(id), uploadForm.file, {
        description: uploadForm.description || undefined,
        source: uploadForm.source || undefined,
        collector_name: uploadForm.collector_name || undefined
      });
      setUploadDialogOpen(false);
      setUploadForm({ file: null, description: '', source: '', collector_name: '' });
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const handleAnalyze = async (evidenceId: number) => {
    setIsAnalyzing(evidenceId);
    try {
      await api.analyzeEvidence(evidenceId);
      await loadData();
    } catch (err) {
      console.error(err);
    } finally {
      setIsAnalyzing(null);
    }
  };

  const handleGenerateReport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;
    
    setIsGeneratingReport(true);
    setError('');
    
    try {
      await api.createReport({
        case_id: parseInt(id),
        report_type: reportForm.report_type,
        title: reportForm.title
      });
      setReportDialogOpen(false);
      setReportForm({ title: '', report_type: 'full_forensic' });
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Report generation failed');
    } finally {
      setIsGeneratingReport(false);
    }
  };

  const getEvidenceAnalysis = (evidenceId: number) => {
    return analysisResults.filter(ar => ar.evidence_id === evidenceId);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!caseData) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-bold text-foreground">Case not found</h2>
        <Link to="/cases">
          <Button variant="outline" className="mt-4">Back to Cases</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate('/cases')}>
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-foreground">{caseData.title}</h1>
              <Badge className={`status-${caseData.status}`}>
                {caseData.status.replace('_', ' ')}
              </Badge>
              <Badge className={`priority-${caseData.priority}`}>
                {caseData.priority}
              </Badge>
            </div>
            <p className="text-muted-foreground">{caseData.case_number}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {user?.role !== 'judge' && (
            isDemoMode ? (
              <>
                <Button variant="outline" onClick={showReadOnlyWarning} className="opacity-60">
                  <Upload className="w-4 h-4 mr-2" />
                  Upload Evidence (Demo)
                </Button>
                <Button onClick={showReadOnlyWarning} className="opacity-60">
                  <FileText className="w-4 h-4 mr-2" />
                  Generate Report (Demo)
                </Button>
              </>
            ) : (
            <>
              <Dialog open={uploadDialogOpen} onOpenChange={setUploadDialogOpen}>
                <DialogTrigger asChild>
                  <Button variant="outline">
                    <Upload className="w-4 h-4 mr-2" />
                    Upload Evidence
                  </Button>
                </DialogTrigger>
                <DialogContent className="bg-card border-border">
                  <DialogHeader>
                    <DialogTitle>Upload Evidence</DialogTitle>
                    <DialogDescription>
                      Upload digital evidence for forensic analysis
                    </DialogDescription>
                  </DialogHeader>
                  <form onSubmit={handleUpload} className="space-y-4">
                    {error && (
                      <Alert variant="destructive">
                        <AlertDescription>{error}</AlertDescription>
                      </Alert>
                    )}
                    <div className="space-y-2">
                      <Label>Evidence File *</Label>
                      <Input
                        type="file"
                        accept="image/*,video/*,audio/*"
                        onChange={(e) => setUploadForm({ ...uploadForm, file: e.target.files?.[0] || null })}
                        required
                        className="bg-input border-border"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Description</Label>
                      <Textarea
                        value={uploadForm.description}
                        onChange={(e) => setUploadForm({ ...uploadForm, description: e.target.value })}
                        placeholder="Describe the evidence"
                        className="bg-input border-border"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Source</Label>
                        <Input
                          value={uploadForm.source}
                          onChange={(e) => setUploadForm({ ...uploadForm, source: e.target.value })}
                          placeholder="e.g., Body camera"
                          className="bg-input border-border"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Collector Name</Label>
                        <Input
                          value={uploadForm.collector_name}
                          onChange={(e) => setUploadForm({ ...uploadForm, collector_name: e.target.value })}
                          placeholder="Who collected this"
                          className="bg-input border-border"
                        />
                      </div>
                    </div>
                    <div className="flex justify-end gap-2">
                      <Button type="button" variant="outline" onClick={() => setUploadDialogOpen(false)}>
                        Cancel
                      </Button>
                      <Button type="submit" disabled={isUploading || !uploadForm.file}>
                        {isUploading ? 'Uploading...' : 'Upload'}
                      </Button>
                    </div>
                  </form>
                </DialogContent>
              </Dialog>

              <Dialog open={reportDialogOpen} onOpenChange={setReportDialogOpen}>
                <DialogTrigger asChild>
                  <Button>
                    <FileText className="w-4 h-4 mr-2" />
                    Generate Report
                  </Button>
                </DialogTrigger>
                <DialogContent className="bg-card border-border">
                  <DialogHeader>
                    <DialogTitle>Generate Forensic Report</DialogTitle>
                    <DialogDescription>
                      Create a court-ready forensic analysis report
                    </DialogDescription>
                  </DialogHeader>
                  <form onSubmit={handleGenerateReport} className="space-y-4">
                    <div className="space-y-2">
                      <Label>Report Title *</Label>
                      <Input
                        value={reportForm.title}
                        onChange={(e) => setReportForm({ ...reportForm, title: e.target.value })}
                        placeholder="Enter report title"
                        required
                        className="bg-input border-border"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Report Type</Label>
                      <Select
                        value={reportForm.report_type}
                        onValueChange={(value) => setReportForm({ ...reportForm, report_type: value })}
                      >
                        <SelectTrigger className="bg-input border-border">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="full_forensic">Full Forensic Report</SelectItem>
                          <SelectItem value="executive_summary">Executive Summary</SelectItem>
                          <SelectItem value="judge_summary">Judge Summary</SelectItem>
                          <SelectItem value="chain_of_custody">Chain of Custody</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="flex justify-end gap-2">
                      <Button type="button" variant="outline" onClick={() => setReportDialogOpen(false)}>
                        Cancel
                      </Button>
                      <Button type="submit" disabled={isGeneratingReport || !reportForm.title}>
                        {isGeneratingReport ? 'Generating...' : 'Generate'}
                      </Button>
                    </div>
                  </form>
                </DialogContent>
              </Dialog>
            </>
            )
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="text-sm">Case Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Type</span>
              <span className="font-medium">{caseData.case_type}</span>
            </div>
            {caseData.incident_date && (
              <div className="flex justify-between">
                <span className="text-muted-foreground flex items-center gap-1">
                  <Calendar className="w-3 h-3" /> Date
                </span>
                <span className="font-medium">
                  {new Date(caseData.incident_date).toLocaleDateString()}
                </span>
              </div>
            )}
            {caseData.incident_location && (
              <div className="flex justify-between">
                <span className="text-muted-foreground flex items-center gap-1">
                  <MapPin className="w-3 h-3" /> Location
                </span>
                <span className="font-medium">{caseData.incident_location}</span>
              </div>
            )}
            <div className="flex justify-between">
              <span className="text-muted-foreground">Created</span>
              <span className="font-medium">
                {new Date(caseData.created_at).toLocaleDateString()}
              </span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="text-sm">Evidence Summary</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Total Items</span>
              <span className="font-medium">{evidence.length}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Analyzed</span>
              <span className="font-medium">
                {evidence.filter(e => e.status === 'analyzed').length}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Pending</span>
              <span className="font-medium">
                {evidence.filter(e => e.status === 'uploaded' || e.status === 'processing').length}
              </span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="text-sm">Reports</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Generated</span>
              <span className="font-medium">{reports.length}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Certified</span>
              <span className="font-medium">
                {reports.filter(r => r.is_certified).length}
              </span>
            </div>
          </CardContent>
        </Card>
      </div>

      {caseData.description && (
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="text-sm">Description</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">{caseData.description}</p>
          </CardContent>
        </Card>
      )}

      <Tabs defaultValue="evidence" className="space-y-4">
        <TabsList className="bg-muted">
          <TabsTrigger value="evidence">
            <FileSearch className="w-4 h-4 mr-2" />
            Evidence ({evidence.length})
          </TabsTrigger>
          <TabsTrigger value="analysis">
            <Shield className="w-4 h-4 mr-2" />
            Analysis ({analysisResults.length})
          </TabsTrigger>
          <TabsTrigger value="reports">
            <FileText className="w-4 h-4 mr-2" />
            Reports ({reports.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="evidence" className="space-y-4">
          {evidence.length === 0 ? (
            <Card className="bg-card border-border">
              <CardContent className="py-12 text-center">
                <FileSearch className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-medium text-foreground mb-2">No evidence uploaded</h3>
                <p className="text-muted-foreground mb-4">
                  Upload digital evidence to begin forensic analysis
                </p>
                {user?.role !== 'judge' && (
                  <Button onClick={() => setUploadDialogOpen(true)}>
                    <Upload className="w-4 h-4 mr-2" />
                    Upload Evidence
                  </Button>
                )}
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              {evidence.map((item) => {
                const Icon = getEvidenceIcon(item.evidence_type);
                const itemAnalysis = getEvidenceAnalysis(item.id);
                const avgConfidence = itemAnalysis.length > 0
                  ? itemAnalysis.reduce((sum, a) => sum + (a.confidence_score || 0), 0) / itemAnalysis.length
                  : null;
                
                return (
                  <Card key={item.id} className="bg-card border-border">
                    <CardContent className="p-4">
                      <div className="flex items-start gap-4">
                        <div className="w-12 h-12 rounded-lg bg-primary/20 flex items-center justify-center flex-shrink-0">
                          <Icon className="w-6 h-6 text-primary" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <h4 className="font-medium text-foreground truncate">
                              {item.original_filename}
                            </h4>
                            <Badge variant="outline" className="capitalize">
                              {item.evidence_type}
                            </Badge>
                            <Badge className={`status-${item.status}`}>
                              {item.status}
                            </Badge>
                          </div>
                          <p className="text-sm text-muted-foreground mb-2">
                            {item.evidence_number} • {(item.file_size / 1024 / 1024).toFixed(2)} MB
                          </p>
                          <div className="flex items-center gap-4 text-xs text-muted-foreground">
                            <span className="flex items-center gap-1">
                              <Hash className="w-3 h-3" />
                              SHA256: {item.sha256_hash.substring(0, 16)}...
                            </span>
                            {item.quality_score !== null && (
                              <span>Quality: {item.quality_score}/100</span>
                            )}
                          </div>
                          {item.quality_issues && item.quality_issues.length > 0 && (
                            <div className="mt-2 flex flex-wrap gap-1">
                              {item.quality_issues.map((issue, i) => (
                                <Badge key={i} variant="outline" className="text-xs text-yellow-400 border-yellow-500/50">
                                  <AlertTriangle className="w-3 h-3 mr-1" />
                                  {issue}
                                </Badge>
                              ))}
                            </div>
                          )}
                          {avgConfidence !== null && (
                            <div className="mt-3">
                              <div className="flex items-center justify-between text-xs mb-1">
                                <span className="text-muted-foreground">Analysis Confidence</span>
                                <span className="font-medium">{avgConfidence.toFixed(1)}%</span>
                              </div>
                              <Progress value={avgConfidence} className="h-2" />
                            </div>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          {user?.role !== 'judge' && item.status === 'uploaded' && (
                            <Button
                              size="sm"
                              onClick={() => handleAnalyze(item.id)}
                              disabled={isAnalyzing === item.id}
                            >
                              {isAnalyzing === item.id ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                              ) : (
                                <Play className="w-4 h-4" />
                              )}
                              <span className="ml-2">Analyze</span>
                            </Button>
                          )}
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => setSelectedEvidence(item)}
                          >
                            Details
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>

        <TabsContent value="analysis" className="space-y-4">
          {analysisResults.length === 0 ? (
            <Card className="bg-card border-border">
              <CardContent className="py-12 text-center">
                <Shield className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-medium text-foreground mb-2">No analysis results</h3>
                <p className="text-muted-foreground">
                  Run analysis on uploaded evidence to see results
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {evidence.map((item) => {
                const itemAnalysis = getEvidenceAnalysis(item.id);
                if (itemAnalysis.length === 0) return null;
                
                return (
                  <Card key={item.id} className="bg-card border-border">
                    <CardHeader>
                      <CardTitle className="text-sm flex items-center gap-2">
                        {item.evidence_number}
                        <span className="text-muted-foreground font-normal">
                          {item.original_filename}
                        </span>
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {itemAnalysis.map((result) => (
                        <div
                          key={result.id}
                          className="p-3 rounded-lg bg-muted/30 border border-border"
                        >
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                              {getStatusIcon(result.status)}
                              <span className="font-medium capitalize">
                                {result.analysis_type.replace(/_/g, ' ')}
                              </span>
                            </div>
                            {result.confidence_tier && (
                              <Badge className={getConfidenceColor(result.confidence_tier)}>
                                {result.confidence_tier} ({result.confidence_score?.toFixed(1)}%)
                              </Badge>
                            )}
                          </div>
                          {result.summary && (
                            <p className="text-sm text-muted-foreground mb-2">
                              {result.summary}
                            </p>
                          )}
                          {result.warnings && result.warnings.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-2">
                              {result.warnings.map((warning, i) => (
                                <Badge key={i} variant="outline" className="text-xs text-yellow-400 border-yellow-500/50">
                                  <AlertTriangle className="w-3 h-3 mr-1" />
                                  {warning}
                                </Badge>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>

        <TabsContent value="reports" className="space-y-4">
          {reports.length === 0 ? (
            <Card className="bg-card border-border">
              <CardContent className="py-12 text-center">
                <FileText className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-medium text-foreground mb-2">No reports generated</h3>
                <p className="text-muted-foreground mb-4">
                  Generate a forensic report after analyzing evidence
                </p>
                {user?.role !== 'judge' && evidence.some(e => e.status === 'analyzed') && (
                  <Button onClick={() => setReportDialogOpen(true)}>
                    <FileText className="w-4 h-4 mr-2" />
                    Generate Report
                  </Button>
                )}
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              {reports.map((report) => (
                <Card key={report.id} className="bg-card border-border">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="font-medium text-foreground">{report.title}</h4>
                        <p className="text-sm text-muted-foreground">
                          {report.report_number} • {report.report_type.replace(/_/g, ' ')}
                        </p>
                        <p className="text-xs text-muted-foreground mt-1">
                          Generated: {new Date(report.created_at).toLocaleString()}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge className={report.status === 'completed' ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'}>
                          {report.status}
                        </Badge>
                        {report.status === 'completed' && (
                          <a
                            href={api.getReportDownloadUrl(report.id)}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            <Button size="sm" variant="outline">
                              <Download className="w-4 h-4 mr-2" />
                              Download PDF
                            </Button>
                          </a>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>

      <Dialog open={!!selectedEvidence} onOpenChange={() => setSelectedEvidence(null)}>
        <DialogContent className="bg-card border-border max-w-2xl">
          <DialogHeader>
            <DialogTitle>Evidence Details</DialogTitle>
            <DialogDescription>
              {selectedEvidence?.evidence_number}
            </DialogDescription>
          </DialogHeader>
          {selectedEvidence && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-muted-foreground">Original Filename</p>
                  <p className="font-medium">{selectedEvidence.original_filename}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Type</p>
                  <p className="font-medium capitalize">{selectedEvidence.evidence_type}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">File Size</p>
                  <p className="font-medium">{(selectedEvidence.file_size / 1024 / 1024).toFixed(2)} MB</p>
                </div>
                <div>
                  <p className="text-muted-foreground">MIME Type</p>
                  <p className="font-medium">{selectedEvidence.mime_type}</p>
                </div>
              </div>
              <div className="space-y-2">
                <p className="text-muted-foreground text-sm">SHA-256 Hash</p>
                <code className="block p-2 rounded bg-muted text-xs break-all">
                  {selectedEvidence.sha256_hash}
                </code>
              </div>
              <div className="space-y-2">
                <p className="text-muted-foreground text-sm">MD5 Hash</p>
                <code className="block p-2 rounded bg-muted text-xs break-all">
                  {selectedEvidence.md5_hash}
                </code>
              </div>
              {selectedEvidence.description && (
                <div>
                  <p className="text-muted-foreground text-sm">Description</p>
                  <p className="text-sm">{selectedEvidence.description}</p>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
