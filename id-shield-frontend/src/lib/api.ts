import type { AuthToken, Case, CaseListResponse, Evidence, EvidenceListResponse, AnalysisResult, Report } from '../types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ApiClient {
  private token: string | null = null;

  constructor() {
    this.token = localStorage.getItem('token');
  }

  setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem('token', token);
    } else {
      localStorage.removeItem('token');
    }
  }

  getToken(): string | null {
    return this.token;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const headers: HeadersInit = {
      ...options.headers,
    };

    if (this.token) {
      (headers as Record<string, string>)['Authorization'] = `Bearer ${this.token}`;
    }

    if (!(options.body instanceof FormData)) {
      (headers as Record<string, string>)['Content-Type'] = 'application/json';
    }

    const response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'An error occurred' }));
      throw new Error(error.detail || 'An error occurred');
    }

    return response.json();
  }

  async login(email: string, password: string): Promise<AuthToken> {
    const response = await this.request<AuthToken>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    this.setToken(response.access_token);
    return response;
  }

  async logout() {
    this.setToken(null);
  }

  async getCurrentUser() {
    return this.request<AuthToken['user']>('/auth/me');
  }

  async getCases(page = 1, pageSize = 20, status?: string, search?: string): Promise<CaseListResponse> {
    const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
    if (status) params.append('status', status);
    if (search) params.append('search', search);
    return this.request<CaseListResponse>(`/cases/?${params}`);
  }

  async getCase(caseId: number): Promise<Case> {
    return this.request<Case>(`/cases/${caseId}`);
  }

  async createCase(data: {
    title: string;
    description?: string;
    case_type: string;
    priority?: string;
    incident_date?: string;
    incident_location?: string;
  }): Promise<Case> {
    return this.request<Case>('/cases/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateCase(caseId: number, data: Partial<Case>): Promise<Case> {
    return this.request<Case>(`/cases/${caseId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async getEvidence(caseId: number): Promise<EvidenceListResponse> {
    return this.request<EvidenceListResponse>(`/evidence/case/${caseId}`);
  }

  async getEvidenceItem(evidenceId: number): Promise<Evidence> {
    return this.request<Evidence>(`/evidence/${evidenceId}`);
  }

  async uploadEvidence(
    caseId: number,
    file: File,
    metadata: { description?: string; source?: string; collector_name?: string }
  ): Promise<Evidence> {
    const formData = new FormData();
    formData.append('file', file);
    if (metadata.description) formData.append('description', metadata.description);
    if (metadata.source) formData.append('source', metadata.source);
    if (metadata.collector_name) formData.append('collector_name', metadata.collector_name);

    return this.request<Evidence>(`/evidence/upload/${caseId}`, {
      method: 'POST',
      body: formData,
    });
  }

  async analyzeEvidence(evidenceId: number): Promise<AnalysisResult[]> {
    return this.request<AnalysisResult[]>(`/evidence/${evidenceId}/analyze`, {
      method: 'POST',
    });
  }

  async getAnalysisResults(evidenceId: number): Promise<AnalysisResult[]> {
    return this.request<AnalysisResult[]>(`/evidence/${evidenceId}/analysis`);
  }

  async getCaseAnalysis(caseId: number): Promise<AnalysisResult[]> {
    return this.request<AnalysisResult[]>(`/analysis/case/${caseId}`);
  }

  async createReport(data: {
    case_id: number;
    report_type: string;
    title: string;
    evidence_ids?: number[];
  }): Promise<Report> {
    return this.request<Report>('/reports/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getCaseReports(caseId: number): Promise<Report[]> {
    return this.request<Report[]>(`/reports/case/${caseId}`);
  }

  async getReport(reportId: number): Promise<Report> {
    return this.request<Report>(`/reports/${reportId}`);
  }

  getReportDownloadUrl(reportId: number): string {
    return `${API_URL}/reports/${reportId}/download`;
  }

  getEvidenceDownloadUrl(evidenceId: number): string {
    return `${API_URL}/evidence/${evidenceId}/download`;
  }
}

export const api = new ApiClient();
