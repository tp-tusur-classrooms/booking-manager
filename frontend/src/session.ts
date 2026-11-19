import { create } from 'zustand';
import { api, onSessionExpired, tokens } from './api';

export type Role = 'user' | 'admin';

export const homeByRole: Record<Role, string> = { user: '/rooms', admin: '/admin' };

export interface User {
  id: string;
  name: string;
  login: string;
  role: Role;
}

interface SignedUser {
  user: User;
  token: string;
  refresh_token: string;
}

type SessionStatus = 'loading' | 'guest' | 'expired' | 'authenticated';

interface SessionState {
  status: SessionStatus;
  user: User | null;
  restore: () => Promise<void>;
  login: (login: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

export const useSession = create<SessionState>((set, get) => ({
  status: 'loading',
  user: null,
  async restore() {
    if (!tokens.access() && !tokens.refresh()) {
      set({ status: 'guest', user: null });
      return;
    }
    try {
      const { data } = await api.get<User>('/profile');
      set({ status: 'authenticated', user: data });
    } catch {
      if (get().status === 'loading') set({ status: 'guest', user: null });
    }
  },
  async login(login, password) {
    const { data } = await api.post<SignedUser>('/auth/login', { login, password });
    tokens.save(data.token, data.refresh_token);
    set({ status: 'authenticated', user: data.user });
  },
  async logout() {
    const refresh = tokens.refresh();
    tokens.clear();
    set({ status: 'guest', user: null });
    if (refresh) await api.post('/auth/logout', { refresh_token: refresh }).catch(() => undefined);
  },
}));

onSessionExpired(() => useSession.setState({ status: 'expired', user: null }));
