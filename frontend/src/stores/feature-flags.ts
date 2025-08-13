import { create } from 'zustand';

const API_URL = 'http://localhost:5000';

interface FeatureFlagsState {
  flags: Record<string, boolean>;
  fetchFlags: () => Promise<void>;
  isLoaded: boolean;
}

export const useFeatureFlagsStore = create<FeatureFlagsState>((set) => ({
  flags: {},
  isLoaded: false,
  fetchFlags: async () => {
    try {
      const response = await fetch(`${API_URL}/api/flags`);
      if (!response.ok) {
        throw new Error('Failed to fetch feature flags');
      }
      const data = await response.json();
      set({ flags: data, isLoaded: true });
    } catch (error) {
      console.error('Failed to fetch feature flags:', error);
      set({ isLoaded: true }); // Mark as loaded even on error to unblock UI
    }
  },
}));