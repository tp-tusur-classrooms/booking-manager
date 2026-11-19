import classroom from '../../assets/classroom.png';
import { plural } from '../../ui';
import type { Classroom } from './api';

export function seats(capacity: number) {
  return `${capacity} ${plural(capacity, ['место', 'места', 'мест'])}`;
}

export function roomSummary(room: Classroom) {
  return `${room.building.name} · ${room.floor} этаж · ${seats(room.capacity)}`;
}

export function equipmentText(room: Classroom) {
  if (room.equipment.length === 0) return 'Оборудование не указано';
  const text = room.equipment.map(({ name }) => name.toLowerCase()).join(' · ');
  return text.charAt(0).toUpperCase() + text.slice(1);
}

export function RoomPhoto({ room, className }: { room: Classroom; className: string }) {
  return (
    <img
      src={room.photo_url ?? classroom}
      alt={room.photo_url ? `Фотография аудитории ${room.number}` : ''}
      className={`bg-illustration object-cover ${className}`}
    />
  );
}
