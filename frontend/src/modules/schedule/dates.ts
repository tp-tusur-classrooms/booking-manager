import type { Lesson } from './api';

const DAY = 24 * 60 * 60 * 1000;

function toUtc(date: string) {
  const [year, month, day] = date.split('-').map(Number);
  return Date.UTC(year, month - 1, day);
}

function fromUtc(time: number) {
  return new Date(time).toISOString().slice(0, 10);
}

export function today() {
  const now = new Date();
  return fromUtc(Date.UTC(now.getFullYear(), now.getMonth(), now.getDate()));
}

export function addDays(date: string, days: number) {
  return fromUtc(toUtc(date) + days * DAY);
}

export function weekday(date: string) {
  return ((new Date(toUtc(date)).getUTCDay() + 6) % 7) + 1;
}

function monday(time: number) {
  return time - (weekday(fromUtc(time)) - 1) * DAY;
}

export function isOddWeek(date: string) {
  const week = monday(toUtc(date));
  const year = new Date(week).getUTCFullYear();
  const thisYear = monday(Date.UTC(year, 8, 1));
  const start = week >= thisYear ? thisYear : monday(Date.UTC(year - 1, 8, 1));
  const number = Math.round((week - start) / (7 * DAY)) + 1;
  return number % 2 === 1;
}

type Recurrence = Pick<Lesson, 'weekday' | 'week_parity' | 'starts_on' | 'ends_on'>;

export function firstOccurrence(lesson: Recurrence) {
  for (let date = lesson.starts_on, step = 0; date <= lesson.ends_on && step < 15; date = addDays(date, 1), step += 1) {
    if (occursOn(lesson, date)) return date;
  }
  return null;
}

export function occursOn(lesson: Recurrence, date: string) {
  if (date < lesson.starts_on || date > lesson.ends_on) return false;
  if (weekday(date) !== lesson.weekday) return false;
  if (lesson.week_parity === 'every') return true;
  return (lesson.week_parity === 'odd') === isOddWeek(date);
}

const longDate = new Intl.DateTimeFormat('ru-RU', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' });

export function formatDate(date: string) {
  return longDate.format(new Date(toUtc(date)));
}
