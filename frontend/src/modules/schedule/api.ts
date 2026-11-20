import { api } from '../../api';
import type { Reference } from '../classrooms/api';

export interface Period {
  id: string;
  order: number;
  start_time: string;
  end_time: string;
}

export interface RoomSummary {
  id: string;
  number: string;
  building: Reference;
}

export interface Lesson {
  id: string;
  room: RoomSummary;
  period: Period;
  date: string;
  starts_at: string;
  ends_at: string;
  subject: string;
  group: string | null;
  teacher: string | null;
}

export interface LessonWrite {
  room_id: string;
  period_id: string;
  date: string;
  subject: string;
  group: string | null;
  teacher: string | null;
}

export interface ClassroomCalendar {
  room: RoomSummary;
  lessons: Lesson[];
}

export interface DaySchedule {
  date: string;
  timezone: string;
  starts_at: string;
  ends_at: string;
  periods: Period[];
  items: ClassroomCalendar[];
}

export const scheduleApi = {
  async schedule(date: string, signal: AbortSignal) {
    const { data } = await api.get<DaySchedule>('/schedule', { params: { date }, signal });
    if (!Array.isArray(data?.items) || !Array.isArray(data?.periods)) throw new Error('Некорректное расписание');
    return data;
  },
  async periods(signal: AbortSignal) {
    const { data } = await api.get<{ items: Period[] }>('/periods', { signal });
    return [...data.items].sort((a, b) => a.order - b.order);
  },
  async lessons(signal: AbortSignal, date?: string) {
    const { data } = await api.get<{ items: Lesson[] }>('/lessons', { signal, params: { date } });
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
