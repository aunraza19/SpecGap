// ============================================
// Upload State Management with Zustand
// ============================================

import { create } from 'zustand';
import type { UploadProgress } from '@/types/api';

interface UploadState {
  files: UploadProgress[];
  projectName: string;
  forceOcr: boolean;
  domain: string;
  isUploading: boolean;
  currentAuditId: string | null;

  // Actions
  addFiles: (files: File[]) => void;
  removeFile: (fileName: string) => void;
  clearFiles: () => void;
  setProjectName: (name: string) => void;
  setForceOcr: (value: boolean) => void;
  setDomain: (domain: string) => void;
  updateFileProgress: (fileName: string, progress: number) => void;
  updateFileStatus: (fileName: string, status: UploadProgress['status'], error?: string) => void;
  addFileLog: (fileName: string, log: string) => void;
  setIsUploading: (value: boolean) => void;
  setCurrentAuditId: (id: string | null) => void;
  reset: () => void;
}

const initialState = {
  files: [],
  projectName: '',
  forceOcr: false,
  domain: 'Software Engineering',
  isUploading: false,
  currentAuditId: null,
};

export const useUploadStore = create<UploadState>((set) => ({
  ...initialState,

  addFiles: (newFiles) =>
    set((state) => {
      const existingNames = new Set(state.files.map((f) => f.file.name));
      const filesToAdd = newFiles
        .filter((f) => !existingNames.has(f.name))
        .map((file) => ({
          file,
          progress: 0,
          status: 'pending' as const,
          logs: [],
        }));
      return { files: [...state.files, ...filesToAdd] };
    }),

  removeFile: (fileName) =>
    set((state) => ({
      files: state.files.filter((f) => f.file.name !== fileName),
    })),

  clearFiles: () => set({ files: [] }),

  setProjectName: (projectName) => set({ projectName }),

  setForceOcr: (forceOcr) => set({ forceOcr }),

  setDomain: (domain) => set({ domain }),

  updateFileProgress: (fileName, progress) =>
    set((state) => ({
      files: state.files.map((f) =>
        f.file.name === fileName ? { ...f, progress } : f
      ),
    })),

  updateFileStatus: (fileName, status, error) =>
    set((state) => ({
      files: state.files.map((f) =>
        f.file.name === fileName ? { ...f, status, error } : f
      ),
    })),

  addFileLog: (fileName, log) =>
    set((state) => ({
      files: state.files.map((f) =>
        f.file.name === fileName
          ? { ...f, logs: [...f.logs, `[${new Date().toLocaleTimeString()}] ${log}`] }
          : f
      ),
    })),

  setIsUploading: (isUploading) => set({ isUploading }),

  setCurrentAuditId: (currentAuditId) => set({ currentAuditId }),

  reset: () => set(initialState),
}));
