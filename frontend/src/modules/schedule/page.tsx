import { Link, useSearchParams } from 'react-router';
import { useSession } from '../../session';
import { primaryButton, secondaryButton, StatePanel } from '../../ui';
import { classroomsApi, type Classroom } from '../classrooms/api';
import { useRequest } from '../classrooms/use-request';
import { periodTime, scheduleApi, type Lesson, type Period } from './api';
import { addDays, formatDate, occursOn, today } from './dates';

const cellLink =
  'block h-full rounded-[10px] outline-accent focus-visible:outline-2 focus-visible:outline-offset-2 [&>div]:hover:border-accent [&>div]:hover:border-solid';

interface ScheduleData {
  rooms: Classroom[];
  periods: Period[];
  lessons: Lesson[];
}

async function loadSchedule(signal: AbortSignal): Promise<ScheduleData> {
  const [rooms, periods, lessons] = await Promise.all([
    classroomsApi.list(signal),
    scheduleApi.periods(signal),
    scheduleApi.lessons(signal),
  ]);
  return { rooms, periods, lessons };
}

function isDate(value: string | null): value is string {
  return value !== null && /^\d{4}-\d{2}-\d{2}$/.test(value) && !Number.isNaN(Date.parse(value));
}

function Arrow({ back }: { back?: boolean }) {
  return (
    <svg aria-hidden="true" viewBox="0 0 20 20" className={`size-5 ${back ? 'rotate-180' : ''}`}>
      <path d="m8 5 5 5-5 5" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function DatePicker({ date, onChange }: { date: string; onChange: (date: string) => void }) {
  return (
    <div className="flex flex-wrap items-end gap-3">
      <label className="flex w-full flex-col gap-2 text-sm leading-5 text-muted sm:w-[280px]">
        Дата
        <input
          type="date"
          required
          value={date}
          onChange={(event) => {
            if (isDate(event.target.value)) onChange(event.target.value);
          }}
          className="h-12 rounded-[10px] border border-line bg-white px-3 text-sm text-ink outline-none focus:border-accent focus:ring-3 focus:ring-accent/20"
        />
      </label>
      <button type="button" aria-label="Предыдущий день" onClick={() => onChange(addDays(date, -1))} className={`${secondaryButton} h-12 w-12 px-0`}>
        <Arrow back />
      </button>
      <button type="button" aria-label="Следующий день" onClick={() => onChange(addDays(date, 1))} className={`${secondaryButton} h-12 w-12 px-0`}>
        <Arrow />
      </button>
      <button type="button" disabled={date === today()} onClick={() => onChange(today())} className={`${secondaryButton} h-12`}>
        Сегодня
      </button>
    </div>
  );
}

function LessonCell({ lesson }: { lesson: Lesson }) {
  const details = [lesson.group, lesson.teacher].filter(Boolean).join(' · ');
  return (
    <div className="flex h-full flex-col justify-center gap-1 rounded-[10px] border border-accent/25 bg-accent-soft px-3 py-2.5">
      <span className="text-[13px] leading-[18px] font-bold">{lesson.subject ?? 'Учебное занятие'}</span>
      {details && <span className="text-xs leading-4 text-muted">{details}</span>}
    </div>
  );
}

function FreeCell() {
  return (
    <div className="flex h-full items-center rounded-[10px] border border-dashed border-line px-3 py-2.5 text-xs leading-4 text-muted">
      Свободно
    </div>
  );
}

function ScheduleTable({ data, date, editable }: { data: ScheduleData; date: string; editable: boolean }) {
  const lessons = data.lessons.filter((lesson) => occursOn(lesson, date));
  const lessonAt = (room: Classroom, period: Period) =>
    lessons.find((lesson) => lesson.room.id === room.id && lesson.period.id === period.id);
  const busyDay = data.rooms.some((room) => data.periods.some((period) => lessonAt(room, period)));

  return (
    <>
      {!busyDay && (
        <p role="status" className="mt-6 rounded-xl bg-white px-5 py-4 text-sm leading-[22px] text-muted ring-1 ring-line">
          Учебных занятий на эту дату нет.
        </p>
      )}
      <div className="mt-6 overflow-x-auto rounded-2xl border border-line bg-white">
        <table
          style={{ minWidth: 168 + data.periods.length * 192 }}
          className="w-full table-fixed border-separate border-spacing-0 text-left text-sm"
        >
          <caption className="sr-only">Расписание на {formatDate(date)}</caption>
          <thead>
            <tr>
              <th scope="col" className="sticky left-0 z-10 w-42 border-b border-line bg-white px-6 py-4 text-xs leading-[18px] font-normal text-muted">
                Аудитория
              </th>
              {data.periods.map((period) => (
                <th key={period.id} scope="col" className="border-b border-line px-2 py-4 text-sm leading-5 font-bold whitespace-nowrap last:pr-6">
                  {periodTime(period)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.rooms.map((room) => (
              <tr key={room.id} className="[&:not(:last-child)>*]:border-b [&>*]:border-line">
                <th scope="row" className="sticky left-0 z-10 bg-white px-6 py-3 align-middle font-normal">
                  <span className="block font-bold whitespace-nowrap">Ауд. {room.number}</span>
                  <span className="block text-xs leading-[18px] whitespace-nowrap text-muted">
                    {room.building.name}
                    {room.status === 'draft' && ' · черновик'}
                  </span>
                </th>
                {data.periods.map((period) => {
                  const lesson = lessonAt(room, period);
                  const place = `Ауд. ${room.number}, ${periodTime(period)}`;
                  const cell = lesson ? <LessonCell lesson={lesson} /> : <FreeCell />;
                  return (
                    <td key={period.id} className="h-[76px] px-2 py-2 align-top last:pr-6">
                      {!editable ? (
                        cell
                      ) : lesson ? (
                        <Link
                          to={`/schedule/${encodeURIComponent(lesson.id)}/edit?date=${date}`}
                          aria-label={`Изменить занятие: ${lesson.subject ?? 'учебное занятие'}, ${place}`}
                          className={cellLink}
                        >
                          {cell}
                        </Link>
                      ) : (
                        <Link
                          to={`/schedule/new?date=${date}&room=${encodeURIComponent(room.id)}&period=${encodeURIComponent(period.id)}`}
                          aria-label={`Добавить занятие: ${place}`}
                          className={cellLink}
                        >
                          {cell}
                        </Link>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

function ScheduleSkeleton() {
  return (
    <div role="status" className="mt-6 rounded-2xl border border-line bg-white p-6 motion-safe:animate-pulse">
      <span className="sr-only">Загружаем расписание</span>
      <div aria-hidden="true" className="flex flex-col gap-4">
        {[0, 1, 2, 3].map((row) => (
          <div key={row} className="flex gap-4">
            <div className="h-12 w-28 shrink-0 rounded bg-line" />
            <div className="h-12 flex-1 rounded-[10px] bg-page" />
            <div className="h-12 flex-1 rounded-[10px] bg-page" />
            <div className="hidden h-12 flex-1 rounded-[10px] bg-page sm:block" />
          </div>
        ))}
      </div>
    </div>
  );
}

export function SchedulePage() {
  const [params, setParams] = useSearchParams();
  const param = params.get('date');
  const date = isDate(param) ? param : today();
  const { result, retry } = useRequest(loadSchedule);
  const isAdmin = useSession((state) => state.user?.role === 'admin');

  const changeDate = (value: string) => setParams({ date: value }, { replace: true });

  return (
    <>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-[32px] leading-10 font-bold">Расписание</h1>
          <p className="mt-2 text-sm leading-[22px] text-muted first-letter:uppercase">{formatDate(date)}</p>
        </div>
        {isAdmin && (
          <Link to={`/schedule/new?date=${date}`} className={`${primaryButton} mt-[13px]`}>
            Добавить занятие
          </Link>
        )}
      </div>
      <div className="mt-8">
        <DatePicker date={date} onChange={changeDate} />
      </div>
      {result.status === 'loading' && <ScheduleSkeleton />}
      {result.status === 'error' && (
        <div className="mt-6">
          <StatePanel alert title="Не удалось загрузить расписание" text="Проверьте подключение к интернету и повторите попытку.">
            <button type="button" onClick={retry} className={primaryButton}>
              Повторить
            </button>
          </StatePanel>
        </div>
      )}
      {result.status === 'ready' && (
        <>
          {result.data.periods.length === 0 ? (
            <div className="mt-6">
              <StatePanel title="Учебные периоды не заданы" text="Расписание появится после настройки учебных периодов." />
            </div>
          ) : result.data.rooms.length === 0 ? (
            <div className="mt-6">
              <StatePanel title="Аудитории пока не добавлены" text="Расписание появится после добавления аудиторий администратором." />
            </div>
          ) : (
            <ScheduleTable data={result.data} date={date} editable={isAdmin} />
          )}
        </>
      )}
    </>
  );
}
