const DAY = 24 * 60 * 60 * 1000;

function toUtc(date: string) {
  const [year, month, day] = date.split('-').map(Number);
  const value = new Date(0);
  value.setUTCFullYear(year, month - 1, day);
  value.setUTCHours(0, 0, 0, 0);
  return value.getTime();
}

function fromUtc(time: number) {
  return new Date(time).toISOString().slice(0, 10);
}

export function today() {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Tomsk', year: 'numeric', month: '2-digit', day: '2-digit',
  }).formatToParts(new Date());
  const value = (type: string) => parts.find((part) => part.type === type)?.value;
  return `${value('year')}-${value('month')}-${value('day')}`;
}

export function addDays(date: string, days: number) {
  return fromUtc(toUtc(date) + days * DAY);
}

export function isDate(value: string | null): value is string {
  if (!value || !/^\d{4}-\d{2}-\d{2}$/.test(value) || value.startsWith('0000')) return false;
  return fromUtc(toUtc(value)) === value;
}

const longDate = new Intl.DateTimeFormat('ru-RU', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' });

export function formatDate(date: string) {
  return longDate.format(new Date(toUtc(date)));
}
