// ============================================
// SpecGap API Client
// ============================================

import type {
  Audit,
  AuditDetail,
  AuditsListParams,
  AuditsListResponse,
  CreateAuditRequest,
  CreateAuditResponse,
  CreateCommentRequest,
  Comment,
  VectorSearchParams,
  VectorSearchResponse,
  CouncilSessionResponse,
  FullSpectrumResponse,
} from '@/types/api';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

// ============================================
// Base Fetch Wrapper
// ============================================

async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  console.log(`[API] Request: ${options.method || 'GET'} ${url}`);

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Network error' }));
    console.error(`[API] Error ${response.status}:`, error);
    throw new Error(error.message || `API Error: ${response.status}`);
  }

  const data = await response.json();
  console.log(`[API] Response ${response.status}:`, data);
  return data;
}

// ============================================
// Audit Endpoints
// ============================================

export const auditApi = {
  // POST /audit/council-session - Quick analysis with flashcards
  councilSession: async (files: File[], domain: string = 'Software Engineering'): Promise<CouncilSessionResponse> => {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));

    const url = `${API_BASE_URL}/audit/council-session?domain=${encodeURIComponent(domain)}`;
    console.log(`[API] Uploading ${files.length} files to ${url}`);

    const response = await fetch(url, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Failed to run council session' }));
      console.error(`[API] Upload Error ${response.status}:`, error);
      throw new Error(error.message || 'Failed to run council session');
    }

    const data = await response.json();
    console.log(`[API] Council Session Success:`, data);
    return data;
  },

  // POST /audit/full-spectrum - Deep analysis with full reports
  fullSpectrum: async (files: File[], domain: string = 'Software Engineering'): Promise<FullSpectrumResponse> => {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));

    const url = `${API_BASE_URL}/audit/full-spectrum?domain=${encodeURIComponent(domain)}`;

    const response = await fetch(url, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Failed to run full spectrum analysis' }));
      throw new Error(error.message || 'Failed to run full spectrum analysis');
    }

    return response.json();
  },

  // POST /audit/agent-swarm - Legacy endpoint (maps to council-session)
  create: async (request: CreateAuditRequest): Promise<CreateAuditResponse> => {
    const formData = new FormData();
    request.files.forEach((file) => formData.append('files', file));
    if (request.project_name) formData.append('project_name', request.project_name);
    if (request.force_ocr) formData.append('force_ocr', 'true');
    if (request.domain) formData.append('domain', request.domain);

    const response = await fetch(`${API_BASE_URL}/audit/council-session?domain=${encodeURIComponent(request.domain || 'Software Engineering')}`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error('Failed to create audit');
    }

    return response.json();
  },

  // GET /audits - List audits with filters
  list: async (params: AuditsListParams = {}): Promise<AuditsListResponse> => {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) searchParams.append(key, String(value));
    });
    return apiFetch(`/audits?${searchParams.toString()}`);
  },

  // GET /audits/:id - Get audit details
  get: async (id: string): Promise<AuditDetail> => {
    return apiFetch(`/audits/${id}`);
  },

  // GET /audits/:id/documents/:file/page/:n - Get document page
  getDocumentPage: async (auditId: string, file: string, page: number): Promise<Blob> => {
    const response = await fetch(
      `${API_BASE_URL}/audits/${auditId}/documents/${file}/page/${page}`
    );
    if (!response.ok) throw new Error('Failed to fetch document page');
    return response.blob();
  },

  // POST /audits/:id/rebuild-index - Trigger index rebuild
  rebuildIndex: async (id: string): Promise<{ status: string }> => {
    return apiFetch(`/audits/${id}/rebuild-index`, { method: 'POST' });
  },

  // POST /audits/:id/rerun - Re-run audit
  rerun: async (id: string): Promise<CreateAuditResponse> => {
    return apiFetch(`/audits/${id}/rerun`, { method: 'POST' });
  },
};


// ============================================
// Vector Search Endpoints
// ============================================

export const vectorApi = {
  // GET /vector/search - Semantic search
  search: async (params: VectorSearchParams): Promise<VectorSearchResponse> => {
    const searchParams = new URLSearchParams({
      q: params.q,
      threshold: String(params.threshold),
    });
    if (params.audit_id) searchParams.append('audit_id', params.audit_id);
    return apiFetch(`/vector/search?${searchParams.toString()}`);
  },

  // POST /vector/add-finding - Add search result as finding
  addAsFinding: async (auditId: string, chunkId: string): Promise<void> => {
    return apiFetch(`/audits/${auditId}/findings/from-vector`, {
      method: 'POST',
      body: JSON.stringify({ chunk_id: chunkId }),
    });
  },
};

// ============================================
// Comments Endpoints
// ============================================

export const commentsApi = {
  // GET /audits/:id/comments - List comments
  list: async (auditId: string): Promise<Comment[]> => {
    return apiFetch(`/audits/${auditId}/comments`);
  },

  // POST /audits/:id/comments - Create comment
  create: async (auditId: string, request: CreateCommentRequest): Promise<Comment> => {
    return apiFetch(`/audits/${auditId}/comments`, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  // PATCH /audits/:id/comments/:commentId - Resolve comment
  resolve: async (auditId: string, commentId: string): Promise<Comment> => {
    return apiFetch(`/audits/${auditId}/comments/${commentId}`, {
      method: 'PATCH',
      body: JSON.stringify({ resolved: true }),
    });
  },
};
