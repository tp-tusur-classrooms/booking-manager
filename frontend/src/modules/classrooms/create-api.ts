import { isAxiosError } from 'axios';
import { api } from '../../api';
import { session, type Classroom } from './api';

export type ClassroomInput = Omit<Classroom, 'id' | 'photo_url'>;
type Option = { id: string; name: string };

export async function getClassroomOptions(signal: AbortSignal) {
  const config = { signal, ...session() };
  const [buildings, equipment] = await Promise.all([
    api.get<Option[]>('/buildings', config),
    api.get<Option[]>('/equipment', config),
  ]);
  if (!Array.isArray(buildings.data) || !Array.isArray(equipment.data)) {
    throw new Error('Некорректные справочники');
  }
  return { buildings: buildings.data, equipment: equipment.data };
}

export async function createClassroom(input: ClassroomInput, photo: File | null) {
  const body = new FormData();
  body.set('number', input.number);
  body.set('building', input.building);
  body.set('floor', String(input.floor));
  body.set('capacity', String(input.capacity));
  body.set('description', input.description);
  for (const item of input.equipment) body.append('equipment', item);
  if (photo) body.set('photo', photo);
  const { data } = await api.post<Classroom>('/classrooms', body, { ...session(), timeout: 30000 });
  if (!data?.id) throw new Error('Некорректный ответ при создании аудитории');
  return data;
}

export function validationDetails(error: unknown) {
  if (!isAxiosError<{ detail?: unknown }>(error)) return [];
  const detail = error.response?.data?.detail;
  return Array.isArray(detail) ? detail as { loc?: string[]; msg?: string }[] : [];
}
