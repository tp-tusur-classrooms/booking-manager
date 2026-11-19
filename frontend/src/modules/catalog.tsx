import { Link } from 'react-router';
import { primaryButton, plural, StatePanel } from '../ui';
import { classroomsApi, type Classroom } from './classrooms/api';
import { equipmentText, RoomPhoto, roomSummary } from './classrooms/room-view';
import { useRequest } from './classrooms/use-request';

const grid = 'mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4';

function RoomCard({ room }: { room: Classroom }) {
  return (
    <li>
      <Link
        to={`/rooms/${encodeURIComponent(room.id)}`}
        className="flex h-full flex-col overflow-hidden rounded-2xl border border-line bg-white outline-accent hover:border-accent/40 focus-visible:outline-2 focus-visible:outline-offset-2"
      >
        <RoomPhoto room={room} className="h-44 w-full" />
        <span className="flex flex-col gap-2.5 p-5">
          <span className="text-xl leading-7 font-bold">Аудитория {room.number}</span>
          <span className="text-xs leading-[18px] text-muted">{roomSummary(room)}</span>
          <span className="text-xs leading-[18px] text-muted">{equipmentText(room)}</span>
        </span>
      </Link>
    </li>
  );
}

function CatalogSkeleton() {
  return (
    <div role="status" className={grid}>
      <span className="sr-only">Загружаем аудитории</span>
      {[0, 1, 2, 3].map((item) => (
        <div
          key={item}
          aria-hidden="true"
          className="overflow-hidden rounded-2xl border border-line bg-white motion-safe:animate-pulse"
        >
          <div className="h-44 bg-illustration" />
          <div className="flex flex-col gap-3 p-5">
            <div className="h-6 w-2/3 rounded bg-line" />
            <div className="h-3 w-5/6 rounded bg-line" />
            <div className="h-3 w-1/2 rounded bg-line" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function CatalogPage() {
  const { result, retry } = useRequest(classroomsApi.list);

  return (
    <>
      <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-2">
        <h1 className="text-[32px] leading-10 font-bold">Каталог аудиторий</h1>
        {result.status === 'ready' && result.data.length > 0 && (
          <p className="text-xs leading-[18px] text-muted">
            {result.data.length} {plural(result.data.length, ['аудитория', 'аудитории', 'аудиторий'])}
          </p>
        )}
      </div>
      {result.status === 'loading' && <CatalogSkeleton />}
      {result.status === 'error' && (
        <div className="mt-8">
          <StatePanel alert title="Не удалось загрузить каталог" text="Проверьте подключение к интернету и повторите попытку.">
            <button type="button" onClick={retry} className={primaryButton}>
              Повторить
            </button>
          </StatePanel>
        </div>
      )}
      {result.status === 'ready' &&
        (result.data.length === 0 ? (
          <div className="mt-8">
            <StatePanel
              title="Аудитории пока не добавлены"
              text="Каталог появится после добавления аудиторий администратором."
            />
          </div>
        ) : (
          <ul className={grid}>
            {result.data.map((room) => (
              <RoomCard key={room.id} room={room} />
            ))}
          </ul>
        ))}
    </>
  );
}
