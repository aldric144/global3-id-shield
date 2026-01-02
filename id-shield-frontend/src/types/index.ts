export interface User {
  id: number;
  uuid: string;
  email: string;
  first_name: string;
  last_name: string;
  badge_number?: string;
  title?: string;
  role: 'admin' | 'supervisor' | 'investigator' | 'judge';
  agency_id: number;
  is_active: boolean;
  is_verified: boolean;
  last_login?: string;
  created_at: string;
}

export interface Agency {
  id: number;
  uuid: string;
  name: string;
  code: string;
  agency_type: string;
  jurisdiction?: string;
  country: string;
  address?: string;
  contact_email?: string;
  contact_phone?: string;
  is_active: boolean;
  data_retention_days: number;
  created_at: string;
}

export interface Case {
  id: number;
  uuid: string;
  case_number: string;
  title: string;
  description?: string;
  case_type: string;
  status: 'open' | 'in_progress' | 'pending_review' | 'closed' | 'archived';
  priority: 'low' | 'medium' | 'high' | 'critical';
  agency_id: number;
  created_by: number;
  assigned_to?: number;
  incident_date?: string;
  incident_location?: string;
  is_sealed: boolean;
  evidence_count: number;
  created_at: string;
  updated_at?: string;
}

export interface Evidence {
  id: number;
  uuid: string;
  evidence_number: string;
  case_id: number;
  uploaded_by: number;
  original_filename: string;
  evidence_type: 'photo' | 'video' | 'audio' | 'screenshot' | 'document';
  mime_type: string;
  file_size: number;
  sha256_hash: string;
  md5_hash: string;
  status: 'uploaded' | 'processing' | 'analyzed' | 'failed' | 'quarantined';
  description?: string;
  source?: string;
  collection_date?: string;
  collection_location?: string;
  collector_name?: string;
  metadata_raw?: Record<string, unknown>;
  is_locked: boolean;
  is_original: boolean;
  quality_score?: number;
  quality_issues?: string[];
  created_at: string;
}

export interface AnalysisResult {
  id: number;
  uuid: string;
  evidence_id: number;
  analysis_type: 'quality_assessment' | 'metadata_extraction' | 'integrity_check' | 'manipulation_detection' | 'identity_consistency' | 'behavioral_analysis' | 'predictive_intelligence';
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  confidence_score?: number;
  confidence_tier?: 'high' | 'moderate' | 'limited' | 'insufficient';
  summary?: string;
  detailed_findings?: Record<string, unknown>;
  warnings?: string[];
  limitations?: string[];
  visual_data?: Record<string, unknown>;
  processing_time_ms?: number;
  model_version?: string;
  is_court_admissible: boolean;
  exclusion_reason?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
}

export interface Report {
  id: number;
  uuid: string;
  report_number: string;
  case_id: number;
  generated_by: number;
  report_type: 'full_forensic' | 'executive_summary' | 'judge_summary' | 'chain_of_custody';
  title: string;
  status: 'generating' | 'completed' | 'failed';
  file_path?: string;
  file_hash?: string;
  included_evidence_ids?: number[];
  summary?: string;
  limitations_section?: string;
  is_certified: boolean;
  certification_hash?: string;
  certified_at?: string;
  created_at: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
  user: User;
}

export interface CaseListResponse {
  cases: Case[];
  total: number;
  page: number;
  page_size: number;
}

export interface EvidenceListResponse {
  evidence: Evidence[];
  total: number;
}

export interface Limitation {
  code: string;
  what: string;
  why: string;
  impact: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
}

export interface SuitabilityTags {
  identity_attribution: 'allowed' | 'not_allowed';
  manipulation_detection: 'strong' | 'moderate' | 'limited';
  timeline_context: 'strong' | 'moderate' | 'limited';
  audio_content: 'strong' | 'moderate' | 'limited' | 'not_reliable' | 'n/a';
}

export interface EvidenceAdmissibility {
  evidence_id: number;
  evidence_uuid: string;
  grade: 'A' | 'B' | 'C' | 'D';
  grade_label: string;
  viability_score: number;
  suitability: SuitabilityTags;
  limitations: Limitation[];
  limitations_count: number;
  thresholds_version: string;
  computed_at: string;
  computed_by?: number;
}
