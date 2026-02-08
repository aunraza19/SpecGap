// ============================================
// React Query Hooks for SpecGap API
// ============================================

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { auditApi, vectorApi, commentsApi } from './client';
import type {
  AuditsListParams,
  CreateAuditRequest,
  CreateCommentRequest,
  VectorSearchParams,
} from '@/types/api';

// ============================================
// Query Keys
// ============================================

export const queryKeys = {
  audits: {
    all: ['audits'] as const,
    list: (params: AuditsListParams) => ['audits', 'list', params] as const,
    detail: (id: string) => ['audits', 'detail', id] as const,
  },
  vector: {
    search: (params: VectorSearchParams) => ['vector', 'search', params] as const,
  },
  comments: {
    list: (auditId: string) => ['comments', auditId] as const,
  },
};

// ============================================
// Audit Hooks
// ============================================

export function useAudits(params: AuditsListParams = {}) {
  return useQuery({
    queryKey: queryKeys.audits.list(params),
    queryFn: () => auditApi.list(params),
  });
}

export function useAudit(id: string) {
  return useQuery({
    queryKey: queryKeys.audits.detail(id),
    queryFn: () => auditApi.get(id),
    enabled: !!id,
  });
}

export function useCreateAudit() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: CreateAuditRequest) => auditApi.create(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.audits.all });
    },
  });
}

export function useRebuildIndex(auditId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => auditApi.rebuildIndex(auditId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.audits.detail(auditId) });
    },
  });
}

export function useRerunAudit(auditId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => auditApi.rerun(auditId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.audits.all });
    },
  });
}

// ============================================
// Vector Search Hooks
// ============================================

export function useVectorSearch(params: VectorSearchParams, enabled = true) {
  return useQuery({
    queryKey: queryKeys.vector.search(params),
    queryFn: () => vectorApi.search(params),
    enabled: enabled && !!params.q,
  });
}

export function useAddFindingFromVector(auditId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (chunkId: string) => vectorApi.addAsFinding(auditId, chunkId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.audits.detail(auditId) });
    },
  });
}

// ============================================
// Comments Hooks
// ============================================

export function useComments(auditId: string) {
  return useQuery({
    queryKey: queryKeys.comments.list(auditId),
    queryFn: () => commentsApi.list(auditId),
    enabled: !!auditId,
  });
}

export function useCreateComment(auditId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: CreateCommentRequest) => commentsApi.create(auditId, request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.comments.list(auditId) });
    },
  });
}

export function useResolveComment(auditId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (commentId: string) => commentsApi.resolve(auditId, commentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.comments.list(auditId) });
    },
  });
}
