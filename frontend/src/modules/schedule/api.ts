import { api } from '../../api';
import type { Reference } from '../classrooms/api';

export interface Period {
  id: string;
  order: number;
  start_time: string;
  end_time: string;
}

export type WeekParity = 'every' | 'odd' | 'even';

export interface RoomSummary {
  id: string;
  number: string;
  building: Reference;
}

export interface Lesson {
  id: string;
  room: RoomSummary;
  period: Period;
  weekday: number;
  week_parity: WeekParity;
  starts_on: string;
  ends_on: string;
  subject: string | null;
  group: string | null;
  teacher: string | null;
}

export interface LessonWrite {
  room_id: string;
  period_id: string;
  weekday: number;
  week_parity: WeekParity;
  starts_on: string;
  ends_on: string;
  subject: string | null;
  group: string | null;
  teacher: string | null;
}

export const scheduleApi = {
  async periods(signal: AbortSignal) {
    const { data } = await api.get<{ items: Period[] }>('/periods', { signal });
    return [...data.items].sort((a, b) => a.order - b.order);
  },
  async lessons(signal: AbortSignal) {
    const { data } = await api.get<{ items: Lesson[] }>('/lessons', { signal });
    return data.items;
  },
  async lesson(id: string, signal: AbortSignal) {
    const { data } = await api.get<Lesson>(`/lessons/${encodeURIComponent(id)}`, { signal });
    return data;
  },
  async create(lesson: LessonWrite) {
    const { data } = await api.post<Lesson>('/lessons', lesson);
    return data;
  },
  async update(id: string, lesson: LessonWrite) {
    const { data } = await api.put<Lesson>(`/lessons/${encodeURIComponent(id)}`, lesson);
    return data;
  },
  async remove(id: string) {
    await api.delete(`/lessons/${encodeURIComponent(id)}`);
  },
};

export function periodTime(period: Period) {
  return `${period.start_time}–${period.end_time}`;
}
