import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface User {
  id: string;
  email: string;
  name: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  signup: (email: string, password: string, name: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
}

// Demo user for hackathon - auto-authenticate
const demoUser: User = {
  id: 'demo-user-001',
  email: 'demo@specgap.ai',
  name: 'Demo User',
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      // Auto-authenticate for demo purposes
      user: demoUser,
      isAuthenticated: true,

      login: async (email, password) => {
        await new Promise((r) => setTimeout(r, 300));
        const user: User = { id: crypto.randomUUID(), email, name: email.split('@')[0] };
        set({ user, isAuthenticated: true });
        return { success: true };
      },

      signup: async (email, password, name) => {
        await new Promise((r) => setTimeout(r, 300));
        const user: User = { id: crypto.randomUUID(), email, name };
        set({ user, isAuthenticated: true });
        return { success: true };
      },

      logout: () => set({ user: null, isAuthenticated: false }),
    }),
    { name: 'specgap-auth' }
  )
);

