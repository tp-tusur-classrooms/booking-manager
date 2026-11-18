import { create } from 'zustand';
import { api } from './api';

type ApiStatus = 'idle' | 'checking' | 'online' | 'offline';

interface ApiStatusState {
  status: ApiStatus;
  check: () => Promise<void>;
}

export const useApiStatus = create<ApiStatusState>((set, get) => ({
  status: 'idle',
  async check() {
    if (get().status === 'checking') return;

    set({ status: 'checking' });
    try {
      const { data } = await api.get<{ status: string }>('/health');
      set({ status: data?.status === 'ok' ? 'online' : 'offline' });
    } catch {
      set({ status: 'offline' });
    }
  },
}));
