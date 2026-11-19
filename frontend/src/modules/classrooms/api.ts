import { isAxiosError } from 'axios';
import { api } from '../../api';

export type Reference = { id: string; name: string };

export type Classroom = {
  id: string;
  number: string;
  building: Reference;
  floor: number;
  capacity: number;
  equipment: Reference[];
  description: string | null;
  photo_url: string | null;
  status: 'draft' | 'published';
};

export type AdminProfile = {
  role?: string;
  name?: string | null;
  unread_notifications?: number;
};

export const classroomsApi = {
  async profile(signal: AbortSignal) {
    const { data } = await api.get<AdminProfile>('/profile', { signal, ...session() });
    return data;
  },
  async list(signal: AbortSignal) {
    const { data } = await api.get<{ items: Classroom[] }>('/rooms', { signal, ...session() });
    if (!Array.isArray(data?.items)) throw new Error('Некорректный список аудиторий');
    return data.items;
  },
  async get(id: string, signal: AbortSignal) {
    const { data } = await api.get<Classroom>(`/rooms/${encodeURIComponent(id)}`, { signal, ...session() });
    if (!data?.id) throw new Error('Некорректная карточка аудитории');
    return data;
  },
};

export function session() {
  const token = sessionStorage.getItem('access_token');
  return token ? { headers: { Authorization: `Bearer ${token}` } } : {};
}

export function requestStatus(error: unknown) {
  return isAxiosError(error) ? error.response?.status : undefined;
}
