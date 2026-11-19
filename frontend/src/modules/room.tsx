import { useCallback } from 'react';
import { Link, useParams } from 'react-router';
import { primaryButton, StatePanel } from '../ui';
import { classroomsApi, requestStatus, type Classroom } from './classrooms/api';
import { equipmentText, RoomPhoto, roomSummary, seats } from './classrooms/room-view';
import { useRequest } from './classrooms/use-request';

function RoomDetails({ room }: { room: Classroom }) {
  return (
    <>
      <h1 className="text-[32px] leading-10 font-bold">Аудитория {room.number}</h1>
      <p className="mt-2 text-sm leading-[22px] text-muted">{roomSummary(room)}</p>
      <div className="mt-8 grid items-start gap-8 lg:grid-cols-[760fr_520fr]">
        <RoomPhoto room={room} className="aspect-[19/8] w-full rounded-2xl" />
        <section aria-labelledby="room-details" className="rounded-2xl border border-line bg-white p-6 sm:p-8">
          <h2 id="room-details" className="sr-only">
            Характеристики
          </h2>
          {room.description && (
            <>
              <p className="text-sm leading-[22px] text-muted">{room.description}</p>
              <hr className="my-6 border-line" />
            </>
          )}
          <dl className="flex flex-col gap-6">
            <div>
              <dt className="sr-only">Вместимость</dt>
              <dd className="text-lg leading-[26px] font-bold">{seats(room.capacity)}</dd>
            </div>
            <div>
              <dt className="sr-only">Оборудование</dt>
              <dd className="text-sm leading-[22px]">{equipmentText(room)}</dd>
            </div>
            <div>
              <dt className="sr-only">Расположение</dt>
              <dd className="text-sm leading-[22px] text-muted">
                {room.building.name}, {room.floor} этаж
              </dd>
            </div>
          </dl>
        </section>
      </div>
    </>
  );
}

function RoomSkeleton() {
  return (
    <div role="status" className="motion-safe:animate-pulse">
      <span className="sr-only">Загружаем аудиторию</span>
      <div aria-hidden="true">
        <div className="h-10 w-64 rounded bg-line" />
        <div className="mt-3 h-4 w-52 rounded bg-line" />
        <div className="mt-8 grid items-start gap-8 lg:grid-cols-[760fr_520fr]">
          <div className="aspect-[19/8] w-full rounded-2xl bg-illustration" />
          <div className="flex flex-col gap-4 rounded-2xl border border-line bg-white p-8">
            <div className="h-4 w-full rounded bg-line" />
            <div className="h-4 w-2/3 rounded bg-line" />
            <div className="mt-4 h-6 w-24 rounded bg-line" />
            <div className="h-4 w-1/2 rounded bg-line" />
          </div>
        </div>
      </div>
    </div>
  );
}

function RoomPage({ id }: { id: string }) {
  const load = useCallback((signal: AbortSignal) => classroomsApi.get(id, signal), [id]);
  const { result, retry } = useRequest(load);

  if (result.status === 'loading') return <RoomSkeleton />;
  if (result.status === 'ready') return <RoomDetails room={result.data} />;

  const status = requestStatus(result.error);
  if (status === 404 || status === 400) {
    return (
      <StatePanel title="Аудитория не найдена" text="Возможно, её убрали из каталога или ссылка устарела.">
        <Link to="/rooms" className={primaryButton}>
          Перейти в каталог
        </Link>
      </StatePanel>
    );
  }

  return (
    <StatePanel alert title="Не удалось загрузить аудиторию" text="Проверьте подключение к интернету и повторите попытку.">
      <button type="button" onClick={retry} className={primaryButton}>
        Повторить
      </button>
    </StatePanel>
  );
}

export function RoomRoute() {
  const { roomId = '' } = useParams();

  return <RoomPage key={roomId} id={roomId} />;
}
