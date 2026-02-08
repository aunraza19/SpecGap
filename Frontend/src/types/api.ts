// ============================================
// SpecGap API Types - Contract Audit Platform
// ============================================

// Audit Status enum
export type AuditStatus =
  | 'processing'
  | 'completed'
  | 'failed'
  | 'pending_review';

// Risk levels for findings
export type RiskLevel = 'critical' | 'high' | 'medium' | 'low' | 'info';

// Finding categories
export type FindingCategory = 'tech_gap' | 'legal_trap' | 'financial_risk' | 'ambiguity';

// ============================================
// Core Audit Types
// ============================================

export interface Audit {
  audit_id: string;
  project_name: string;
  status: AuditStatus;
  created_at: string;
  updated_at?: string;
  ambiguity_score: number;
  leverage_score: number;
  risk_score?: number;
  document_count?: number;
  finding_count?: number;
}

export interface AuditDetail extends Audit {
  tech_gaps: any;       // Backend: tech_gaps (JSON)
  proposal_risks: any;  // Backend: proposal_risks (JSON)
  contradictions: any;  // Backend: contradictions (JSON)
  patch_pack: any;      // Backend: patch_pack (JSON)
  // Missing from backend AuditRecord:
  // mermaid?: string; 
  // documents: AuditDocument[];
  // comments: Comment[];
}

export interface TechReport {
  summary: string;
  findings: Finding[];
  tech_stack_identified: string[];
  feasibility_score: number;
}

export interface LegalReport {
  summary: string;
  findings: Finding[];
  contract_type: string;
  jurisdiction?: string;
  risk_areas: string[];
}

export interface PatchPack {
  id: string;
  generated_at: string;
  patches: Patch[];
  redline_content?: string;
  email_draft?: string;
}

export interface Patch {
  id: string;
  finding_id: string;
  original_text: string;
  proposed_text: string;
  rationale: string;
  applied: boolean;
}

// ============================================
// Finding Types
// ============================================

export interface Finding {
  id: string;
  category: FindingCategory;
  title: string;
  description: string;
  risk_level: RiskLevel;
  quote: string;
  source_file: string;
  page: number;
  start_index?: number;
  end_index?: number;
  agent_source: 'legal' | 'business' | 'finance';
  recommendations: string[];
  related_findings?: string[];
}

export interface FindingHighlight {
  page: number;
  startIndex: number;
  endIndex: number;
  quote: string;
  findingId: string;
  riskLevel: RiskLevel;
}

// ============================================
// Document Types
// ============================================

export interface AuditDocument {
  id: string;
  filename: string;
  file_type: 'pdf' | 'docx' | 'txt';
  page_count: number;
  size_bytes: number;
  uploaded_at: string;
  ocr_processed: boolean;
  thumbnail_url?: string;
}

// ============================================
// Vector Search Types
// ============================================

export interface VectorSearchResult {
  chunk_id: string;
  source_file: string;
  page: number;
  snippet: string;
  similarity_score: number;
  audit_id?: string;
}

export interface VectorSearchParams {
  q: string;
  audit_id?: string;
  threshold: number;
}

// ============================================
// Comment Types
// ============================================

export interface Comment {
  id: string;
  finding_id?: string;
  audit_id: string;
  text: string;
  author: string;
  created_at: string;
  resolved: boolean;
}

// ============================================
// API Request/Response Types
// ============================================

// POST /audit/agent-swarm
export interface CreateAuditRequest {
  files: File[];
  project_name?: string;
  force_ocr?: boolean;
  domain?: string;
}

export interface CreateAuditResponse {
  audit_id: string;
  status: 'processing';
}

// GET /audits
export interface AuditsListParams {
  page?: number;
  limit?: number;
  q?: string;
  status?: AuditStatus;
  date_from?: string;
  date_to?: string;
  min_score?: number;
  max_score?: number;
}

export interface AuditHistoryItem {
  id: string;
  created_at: string;
  project_name: string | null;
  audit_type: string;
  risk_level: string | null;
  composite_risk_score: number | null;
}

export interface AuditsListResponse {
  status: string;
  audits: AuditHistoryItem[];
  total: number;
  limit: number;
  offset: number;
}

// GET /vector/search
export interface VectorSearchResponse {
  results: VectorSearchResult[];
  query: string;
  threshold: number;
  total: number;
}

// POST /audits/:id/comments
export interface CreateCommentRequest {
  finding_id?: string;
  text: string;
}

// Upload progress tracking
export interface UploadProgress {
  file: File;
  progress: number;
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'error';
  error?: string;
  logs: string[];
}

// Agent Council visualization
export interface AgentState {
  id: 'legal' | 'business' | 'finance';
  name: string;
  status: 'idle' | 'reading' | 'debating' | 'finalizing' | 'complete';
  avatar: string;
  color: string;
}

export interface CouncilSession {
  round: 1 | 2 | 3;
  agents: AgentState[];
  connections: Array<[string, string]>;
  progress: number;
}

// ============================================
// Flashcard Types (from Council Session)
// ============================================

export type FlashcardSeverity = 'Critical' | 'High' | 'Medium' | 'Low' | 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';

export interface Flashcard {
  id: string;
  card_type: string;
  title: string;
  description: string;
  fix_action: string;
  severity: FlashcardSeverity;
  swipe_right_payload: string;
  source_agent: 'legal' | 'business' | 'finance';
}

export interface CouncilSessionResponse {
  status: 'success' | 'error';
  files_analyzed: string[];
  domain: string;
  council_verdict: {
    flashcards: Flashcard[];
  };
  message?: string;
  details?: string;
}

export interface FullSpectrumResponse extends CouncilSessionResponse {
  mode: 'full_spectrum';
  deep_analysis: {
    tech_audit: {
      project_name: string;
      critical_gaps: Array<{
        feature: string;
        missing_component: string;
        risk_level: string;
        recommendation: string;
        source_reference: string;
      }>;
      ambiguity_score: number;
    };
    legal_audit: {
      leverage_score: number;
      favor_direction: string;
      trap_clauses: Array<{
        clause_snippet: string;
        risk_explanation: string;
        severity: string;
        redline_suggestion: {
          original_text: string;
          proposed_text: string;
          negotiation_argument: string;
        };
      }>;
      negotiation_tips: string[];
    };
    executive_synthesis: {
      contradictions: Array<{
        topic: string;
        document_a_says?: string;
        document_b_says?: string;
        impact: string;
        // Legacy fallback
        issue?: string;
        description?: string;
      }>;
      strategic_synthesis: string;
      reality_diagram_mermaid?: string;
      patch_pack?: {
        jira_tickets: Array<{
          title: string;
          description: string;
          priority: string;
          labels: string[];
          acceptance_criteria: string;
        }>;
        negotiation_email: string;
      };
    };
  };
}
