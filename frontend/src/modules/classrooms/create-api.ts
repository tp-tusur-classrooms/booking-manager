import { isAxiosError } from 'axios';
import { api } from '../../api';
import { session, type Classroom, type Reference } from './api';

type ClassroomInput = {
  number: string;
  building_id: string;
  floor: number;
  capacity: number;
  equipment_ids: string[];
  description: string | null;
};

export async function getClassroomOptions(signal: AbortSignal) {
  const config = { signal, ...session() };
  const [buildings, equipment] = await Promise.all([
    api.get<{ items: Reference[] }>('/buildings', config),
    api.get<{ items: Reference[] }>('/equipment', config),
  ]);
  if (!Array.isArray(buildings.data?.items) || !Array.isArray(equipment.data?.items)) {
    throw new Error('Некорректные справочники');
  }
  return { buildings: buildings.data.items, equipment: equipment.data.items };
}

export async function createClassroom(input: ClassroomInput) {
  const { data } = await api.post<Classroom>('/rooms', input, session());
  if (!data?.id) throw new Error('Некорректный ответ при создании аудитории');
  return data.id;
}

export async function uploadClassroomPhoto(id: string, photo: File) {
  const body = new FormData();
  body.set('file', photo);
  await api.put(`/rooms/${encodeURIComponent(id)}/photo`, body, { ...session(), timeout: 30000 });
}

export async function publishClassroom(id: string) {
  const { data } = await api.post<Classroom>(`/rooms/${encodeURIComponent(id)}/publish`, undefined, session());
  if (data?.status !== 'published') throw new Error('Аудитория не опубликована');
}

export function validationDetails(error: unknown) {
  if (!isAxiosError<{ errors?: { field: string; message: string }[] }>(error)) return [];
  const issues = error.response?.data?.errors;
  return Array.isArray(issues) ? issues : [];
}
