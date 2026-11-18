import { isAxiosError } from 'axios';
import { api } from '../../api';

export type Classroom = {
  id: string;
  number: string;
  building: string;
  floor: number;
  capacity: number;
  equipment: string[];
  description: string;
  photo_url?: string | null;
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
    const { data } = await api.get<Classroom[]>('/classrooms', { signal, ...session() });
    if (!Array.isArray(data)) throw new Error('Некорректный список аудиторий');
    return data;
  },
  async get(id: string, signal: AbortSignal) {
    const { data } = await api.get<Classroom>(`/classrooms/${encodeURIComponent(id)}`, { signal, ...session() });
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
