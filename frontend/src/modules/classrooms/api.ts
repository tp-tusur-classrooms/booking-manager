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

export const classroomsApi = {
  async list(signal: AbortSignal) {
    const { data } = await api.get<{ items: Classroom[] }>('/rooms', { signal });
    if (!Array.isArray(data?.items)) throw new Error('Некорректный список аудиторий');
    return data.items;
  },
  async get(id: string, signal: AbortSignal) {
    const { data } = await api.get<Classroom>(`/rooms/${encodeURIComponent(id)}`, { signal });
    if (!data?.id) throw new Error('Некорректная карточка аудитории');
    return data;
  },
};

export function requestStatus(error: unknown) {
  return isAxiosError(error) ? error.response?.status : undefined;
}
