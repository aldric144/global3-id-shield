import { createContext, useContext, ReactNode } from 'react';
import type { User, Case, Evidence, AnalysisResult, Report, Agency } from '../types';

export const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true';

export const DEMO_USER: User = {
  id: 1,
  uuid: 'demo-user-uuid-001',
  email: 'demo.investigator@global3ti.com',
  first_name: 'Demo',
  last_name: 'Investigator',
  badge_number: 'DEMO-001',
  title: 'Forensic Analyst',
  role: 'investigator',
  agency_id: 1,
  is_active: true,
  is_verified: true,
  last_login: new Date().toISOString(),
  created_at: '2024-01-01T00:00:00Z',
};

export const DEMO_AGENCY: Agency = {
  id: 1,
  uuid: 'demo-agency-uuid-001',
  name: 'Global3 Technology & Intelligence',
  code: 'G3TI',
  agency_type: 'federal',
  jurisdiction: 'International',
  country: 'United States',
  address: '1234 Intelligence Way, Washington DC',
  contact_email: 'contact@global3ti.com',
  contact_phone: '+1-555-0100',
  is_active: true,
  data_retention_days: 365,
  created_at: '2024-01-01T00:00:00Z',
};

export const DEMO_CASES: Case[] = [
  {
    id: 1,
    uuid: 'case-uuid-001',
    case_number: 'G3TI-2024-001',
    title: 'Digital Evidence Authentication - Operation Clarity',
    description: 'Investigation into potential digital manipulation of surveillance footage from multiple sources. Evidence includes video recordings, photographs, and audio files requiring forensic analysis.',
    case_type: 'homicide',
    status: 'in_progress',
    priority: 'high',
    agency_id: 1,
    created_by: 1,
    assigned_to: 1,
    incident_date: '2024-11-15T14:30:00Z',
    incident_location: 'Downtown District, Metro City',
    is_sealed: false,
    evidence_count: 5,
    created_at: '2024-11-16T09:00:00Z',
    updated_at: '2024-12-20T15:30:00Z',
  },
  {
    id: 2,
    uuid: 'case-uuid-002',
    case_number: 'G3TI-2024-002',
    title: 'Identity Verification - Financial Fraud Investigation',
    description: 'Analysis of submitted identity documents and video recordings to verify authenticity and detect potential deepfake manipulation.',
    case_type: 'fraud',
    status: 'pending_review',
    priority: 'medium',
    agency_id: 1,
    created_by: 1,
    assigned_to: 1,
    incident_date: '2024-10-20T10:00:00Z',
    incident_location: 'Financial District',
    is_sealed: false,
    evidence_count: 3,
    created_at: '2024-10-21T08:00:00Z',
    updated_at: '2024-12-18T11:00:00Z',
  },
  {
    id: 3,
    uuid: 'case-uuid-003',
    case_number: 'G3TI-2024-003',
    title: 'Media Integrity Assessment - Public Safety',
    description: 'Forensic examination of viral media content to determine authenticity and identify potential manipulation or synthetic generation.',
    case_type: 'public_safety',
    status: 'open',
    priority: 'critical',
    agency_id: 1,
    created_by: 1,
    incident_date: '2024-12-10T16:45:00Z',
    incident_location: 'Multiple Locations',
    is_sealed: false,
    evidence_count: 8,
    created_at: '2024-12-11T07:00:00Z',
    updated_at: '2024-12-19T14:00:00Z',
  },
];

export const DEMO_EVIDENCE: Evidence[] = [
  {
    id: 1,
    uuid: 'evidence-uuid-001',
    evidence_number: 'EVD-2024-001-A',
    case_id: 1,
    uploaded_by: 1,
    original_filename: 'surveillance_cam_01.mp4',
    evidence_type: 'video',
    mime_type: 'video/mp4',
    file_size: 125829120,
    sha256_hash: 'a7b9c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2',
    md5_hash: '1a2b3c4d5e6f7g8h9i0j1k2l',
    status: 'analyzed',
    description: 'Primary surveillance footage from entrance camera',
    source: 'Building Security System',
    collection_date: '2024-11-15T15:00:00Z',
    collection_location: 'Main Entrance',
    collector_name: 'Officer J. Smith',
    is_locked: true,
    is_original: true,
    quality_score: 87,
    quality_issues: ['Minor compression artifacts'],
    created_at: '2024-11-16T09:30:00Z',
  },
  {
    id: 2,
    uuid: 'evidence-uuid-002',
    evidence_number: 'EVD-2024-001-B',
    case_id: 1,
    uploaded_by: 1,
    original_filename: 'witness_photo_01.jpg',
    evidence_type: 'photo',
    mime_type: 'image/jpeg',
    file_size: 4194304,
    sha256_hash: 'b8c9d0e1f2g3h4i5j6k7l8m9n0o1p2q3r4s5t6u7v8w9x0y1z2a3b4c5d6e7f8g9',
    md5_hash: '2b3c4d5e6f7g8h9i0j1k2l3m',
    status: 'analyzed',
    description: 'Photograph submitted by witness',
    source: 'Witness Statement',
    collection_date: '2024-11-15T16:30:00Z',
    collection_location: 'Police Station',
    collector_name: 'Detective M. Johnson',
    is_locked: true,
    is_original: true,
    quality_score: 92,
    created_at: '2024-11-16T10:00:00Z',
  },
  {
    id: 3,
    uuid: 'evidence-uuid-003',
    evidence_number: 'EVD-2024-001-C',
    case_id: 1,
    uploaded_by: 1,
    original_filename: 'audio_recording.wav',
    evidence_type: 'audio',
    mime_type: 'audio/wav',
    file_size: 52428800,
    sha256_hash: 'c9d0e1f2g3h4i5j6k7l8m9n0o1p2q3r4s5t6u7v8w9x0y1z2a3b4c5d6e7f8g9h0',
    md5_hash: '3c4d5e6f7g8h9i0j1k2l3m4n',
    status: 'analyzed',
    description: 'Audio recording from interview',
    source: 'Interview Room Recording',
    collection_date: '2024-11-16T11:00:00Z',
    collection_location: 'Interview Room 3',
    collector_name: 'Detective M. Johnson',
    is_locked: true,
    is_original: true,
    quality_score: 78,
    quality_issues: ['Background noise detected', 'Some audio clipping'],
    created_at: '2024-11-16T12:00:00Z',
  },
];

export const DEMO_ANALYSIS_RESULTS: AnalysisResult[] = [
  {
    id: 1,
    uuid: 'analysis-uuid-001',
    evidence_id: 1,
    analysis_type: 'quality_assessment',
    status: 'completed',
    confidence_score: 87,
    confidence_tier: 'moderate',
    summary: 'Video quality is sufficient for forensic analysis. Minor compression artifacts detected but do not impact integrity assessment.',
    detailed_findings: {
      resolution: '1920x1080',
      frame_rate: 30,
      bitrate: '8 Mbps',
      duration: '00:15:32',
      codec: 'H.264',
    },
    warnings: ['Compression artifacts may affect fine detail analysis'],
    limitations: ['Night vision mode reduces color accuracy'],
    processing_time_ms: 2340,
    model_version: '1.0.0-MVP',
    is_court_admissible: true,
    started_at: '2024-11-16T09:35:00Z',
    completed_at: '2024-11-16T09:35:02Z',
    created_at: '2024-11-16T09:35:00Z',
  },
  {
    id: 2,
    uuid: 'analysis-uuid-002',
    evidence_id: 1,
    analysis_type: 'integrity_check',
    status: 'completed',
    confidence_score: 94,
    confidence_tier: 'high',
    summary: 'No evidence of tampering or manipulation detected. File integrity verified through cryptographic hash analysis.',
    detailed_findings: {
      hash_verified: true,
      metadata_consistent: true,
      timestamp_valid: true,
      no_splice_detected: true,
    },
    processing_time_ms: 1850,
    model_version: '1.0.0-MVP',
    is_court_admissible: true,
    started_at: '2024-11-16T09:36:00Z',
    completed_at: '2024-11-16T09:36:02Z',
    created_at: '2024-11-16T09:36:00Z',
  },
  {
    id: 3,
    uuid: 'analysis-uuid-003',
    evidence_id: 1,
    analysis_type: 'manipulation_detection',
    status: 'completed',
    confidence_score: 91,
    confidence_tier: 'high',
    summary: 'No indicators of digital manipulation, deepfake generation, or synthetic content detected.',
    detailed_findings: {
      gan_artifacts: false,
      pixel_inconsistencies: false,
      lighting_anomalies: false,
      facial_consistency: true,
      temporal_consistency: true,
    },
    processing_time_ms: 8920,
    model_version: '1.0.0-MVP',
    is_court_admissible: true,
    started_at: '2024-11-16T09:37:00Z',
    completed_at: '2024-11-16T09:37:09Z',
    created_at: '2024-11-16T09:37:00Z',
  },
  {
    id: 4,
    uuid: 'analysis-uuid-004',
    evidence_id: 2,
    analysis_type: 'quality_assessment',
    status: 'completed',
    confidence_score: 92,
    confidence_tier: 'high',
    summary: 'Image quality is excellent for forensic analysis. High resolution with minimal artifacts.',
    detailed_findings: {
      resolution: '4032x3024',
      format: 'JPEG',
      color_depth: '24-bit',
      dpi: 300,
    },
    processing_time_ms: 890,
    model_version: '1.0.0-MVP',
    is_court_admissible: true,
    started_at: '2024-11-16T10:05:00Z',
    completed_at: '2024-11-16T10:05:01Z',
    created_at: '2024-11-16T10:05:00Z',
  },
];

export const DEMO_REPORTS: Report[] = [
  {
    id: 1,
    uuid: 'report-uuid-001',
    report_number: 'RPT-2024-001-FULL',
    case_id: 1,
    generated_by: 1,
    report_type: 'full_forensic',
    title: 'Full Forensic Analysis Report - Case G3TI-2024-001',
    status: 'completed',
    file_path: '/reports/RPT-2024-001-FULL.pdf',
    file_hash: 'rpt-hash-001',
    included_evidence_ids: [1, 2, 3],
    summary: 'Comprehensive forensic analysis of all submitted evidence. All items verified as authentic with high confidence.',
    limitations_section: 'Analysis limited to digital forensic examination. Physical evidence examination not included.',
    is_certified: true,
    certification_hash: 'cert-hash-001',
    certified_at: '2024-12-15T14:00:00Z',
    created_at: '2024-12-15T13:30:00Z',
  },
  {
    id: 2,
    uuid: 'report-uuid-002',
    report_number: 'RPT-2024-001-EXEC',
    case_id: 1,
    generated_by: 1,
    report_type: 'executive_summary',
    title: 'Executive Summary - Case G3TI-2024-001',
    status: 'completed',
    file_path: '/reports/RPT-2024-001-EXEC.pdf',
    file_hash: 'rpt-hash-002',
    included_evidence_ids: [1, 2, 3],
    summary: 'High-level summary of forensic findings suitable for executive briefing.',
    is_certified: true,
    certification_hash: 'cert-hash-002',
    certified_at: '2024-12-15T14:30:00Z',
    created_at: '2024-12-15T14:15:00Z',
  },
];

interface DemoContextType {
  isDemoMode: boolean;
  isReadOnly: boolean;
  demoUser: User;
  demoAgency: Agency;
  demoCases: Case[];
  demoEvidence: Evidence[];
  demoAnalysisResults: AnalysisResult[];
  demoReports: Report[];
  showReadOnlyWarning: () => void;
}

const DemoContext = createContext<DemoContextType | undefined>(undefined);

export function DemoProvider({ children }: { children: ReactNode }) {
  const showReadOnlyWarning = () => {
    alert('Demo Mode: This action is disabled in read-only demo mode. Full functionality will be available when connected to the backend.');
  };

  return (
    <DemoContext.Provider
      value={{
        isDemoMode: DEMO_MODE,
        isReadOnly: DEMO_MODE,
        demoUser: DEMO_USER,
        demoAgency: DEMO_AGENCY,
        demoCases: DEMO_CASES,
        demoEvidence: DEMO_EVIDENCE,
        demoAnalysisResults: DEMO_ANALYSIS_RESULTS,
        demoReports: DEMO_REPORTS,
        showReadOnlyWarning,
      }}
    >
      {children}
    </DemoContext.Provider>
  );
}

export function useDemo() {
  const context = useContext(DemoContext);
  if (context === undefined) {
    throw new Error('useDemo must be used within a DemoProvider');
  }
  return context;
}
