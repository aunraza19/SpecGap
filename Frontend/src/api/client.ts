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

  // POST /audit/council-session/stream - Real-time analysis
  councilSessionStream: async (
    files: File[],
    domain: string = 'Software Engineering',
    onEvent: (event: any) => void
  ): Promise<void> => {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));

    const url = `${API_BASE_URL}/audit/council-session/stream?domain=${encodeURIComponent(domain)}`;
    console.log(`[API] Stream Request: ${url}`);

    try {
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
        // No Content-Type header needed for FormData, browser sets it with boundary
      });

      if (!response.ok) {
        throw new Error(`Stream Error: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error("Response body is not readable");

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");

        // Process clear lines, keep incomplete one in buffer
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const jsonStr = line.slice(6);
            try {
              const event = JSON.parse(jsonStr);
              onEvent(event);
            } catch (e) {
              console.error("Failed to parse SSE event:", jsonStr, e);
            }
          }
        }
      }
    } catch (error) {
      console.error("[API] Stream failed:", error);
      throw error;
    }
  },

  // POST /audit/full-spectrum/stream
  fullSpectrumStream: async (
    files: File[],
    domain: string = 'Software Engineering',
    onEvent: (event: any) => void
  ): Promise<void> => {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));

    const url = `${API_BASE_URL}/audit/full-spectrum/stream?domain=${encodeURIComponent(domain)}`;
    console.log(`[API] Stream Request: ${url}`);

    try {
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Stream Error: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error("Response body is not readable");

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");

        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const jsonStr = line.slice(6);
            try {
              const event = JSON.parse(jsonStr);
              onEvent(event);
            } catch (e) {
              console.error("Failed to parse SSE event:", jsonStr, e);
            }
          }
        }
      }
    } catch (error) {
      console.error("[API] Stream failed:", error);
      throw error;
    }
  },

  // POST /audit/deep-analysis - Deep analysis WITHOUT redundant flashcards
  deepAnalysis: async (
    files: File[],
    domain: string = 'Software Engineering',
    onEvent: (event: any) => void
  ): Promise<void> => {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));

    const url = `${API_BASE_URL}/audit/deep-analysis?domain=${encodeURIComponent(domain)}`;
    console.log(`[API] Deep Analysis Request: ${url}`);

    // Simulate stage progression for the UI
    onEvent({ type: 'stage', stage: 'tech_audit' });

    const response = await fetch(url, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Deep analysis failed' }));
      onEvent({ type: 'error', message: error.message || 'Deep analysis failed' });
      throw new Error(error.message || 'Deep analysis failed');
    }

    onEvent({ type: 'stage', stage: 'legal_audit' });
    const result = await response.json();
    onEvent({ type: 'stage', stage: 'synthesis' });

    // Normalize UPPERCASE keys from LLM responses to lowercase
    const rawSynthesis = result.executive_synthesis || {};
    const normalizedSynthesis = {
      contradictions: rawSynthesis.CONTRADICTIONS || rawSynthesis.contradictions || [],
      strategic_synthesis: rawSynthesis.STRATEGIC_SYNTHESIS || rawSynthesis.strategic_synthesis || '',
      reality_diagram_mermaid: rawSynthesis.REALITY_DIAGRAM_MERMAID || rawSynthesis.reality_diagram_mermaid || '',
      patch_pack: rawSynthesis.PATCH_PACK || rawSynthesis.patch_pack || null,
    };

    // Wrap deep-analysis response so the frontend can handle it
    // Deep analysis has no council_verdict, so we set it to null
    const wrappedResult = {
      ...result,
      council_verdict: result.council_verdict || null,
      deep_analysis: {
        tech_audit: result.tech_audit,
        legal_audit: result.legal_audit,
        executive_synthesis: normalizedSynthesis,
      }
    };

    onEvent({ type: 'complete', result: wrappedResult });
  },

  // POST /audit/full-spectrum - Full spectrum with council + deep
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


// ============================================
// Queue Management Endpoints
// ============================================

export interface QueueInfo {
  queue_length: number;
  is_processing: boolean;
  estimated_wait_seconds: number;
  daily_quota: {
    used: number;
    limit: number;
    remaining: number;
    is_exhausted: boolean;
    resets_at: string;
  };
}

export interface QueueEntry {
  id: string;
  session_id: string;
  status: 'waiting' | 'processing' | 'completed' | 'failed' | 'timeout' | 'cancelled';
  position: number;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
  wait_time?: {
    wait_seconds: number;
    wait_formatted: string;
  };
}

export interface EnqueueResponse {
  status: string;
  entry: QueueEntry;
  queue_info: QueueInfo;
  message: string;
}

export const queueApi = {
  // GET /queue/info - Get current queue status
  getInfo: async (): Promise<QueueInfo> => {
    return apiFetch('/queue/info');
  },

  // POST /queue/enqueue - Join the queue
  enqueue: async (domain: string = 'Software Engineering'): Promise<EnqueueResponse> => {
    return apiFetch(`/queue/enqueue?domain=${encodeURIComponent(domain)}`, {
      method: 'POST',
    });
  },

  // GET /queue/status - Get your queue position
  getStatus: async (): Promise<{ status: string; entry?: QueueEntry; queue_info: QueueInfo; message?: string }> => {
    return apiFetch('/queue/status');
  },

  // DELETE /queue/cancel/:entryId - Cancel your queue entry
  cancel: async (entryId: string): Promise<{ status: string; message: string }> => {
    return apiFetch(`/queue/cancel/${entryId}`, {
      method: 'DELETE',
    });
  },

  // POST /audit/council-session/queued - Queue-managed streaming analysis (RECOMMENDED)
  queuedCouncilSessionStream: async (
    files: File[],
    domain: string = 'Software Engineering',
    onEvent: (event: QueueStreamEvent) => void
  ): Promise<void> => {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));

    const url = `${API_BASE_URL}/audit/council-session/queued?domain=${encodeURIComponent(domain)}`;
    console.log(`[API] Queued Stream Request: ${url}`);

    try {
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
        credentials: 'include', // Important: Include cookies for session tracking
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ message: 'Stream Error' }));
        throw new Error(error.message || `Stream Error: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error("Response body is not readable");

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");

        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const jsonStr = line.slice(6);
            try {
              const event = JSON.parse(jsonStr);
              onEvent(event);
            } catch (e) {
              console.error("Failed to parse SSE event:", jsonStr, e);
            }
          }
        }
      }
    } catch (error) {
      console.error("[API] Queued Stream failed:", error);
      throw error;
    }
  },
};

// Event types for queued streaming
export type QueueStreamEvent =
  | { type: 'queue'; position: number; wait_time: { wait_seconds: number; wait_formatted: string }; queue_info?: QueueInfo }
  | { type: 'stage'; stage: 'starting' | 'council' | 'round1' | 'round2' | 'round3' | 'synthesis'; message?: string }
  | { type: 'complete'; result: CouncilSessionResponse }
  | { type: 'error'; message: string }
  | { type: 'info'; message: string };

