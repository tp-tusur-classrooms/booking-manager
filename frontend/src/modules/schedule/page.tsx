import { useCallback } from 'react';
import { Link, useSearchParams } from 'react-router';
import { useSession } from '../../session';
import { primaryButton, secondaryButton, StatePanel } from '../../ui';
import { useRequest } from '../classrooms/use-request';
import { periodTime, scheduleApi, type DaySchedule, type Lesson, type Period } from './api';
import { addDays, formatDate, isDate, today } from './dates';

const cellLink =
  'block h-full rounded-[10px] outline-accent focus-visible:outline-2 focus-visible:outline-offset-2 [&>div]:hover:border-accent [&>div]:hover:border-solid';

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

function ScheduleTable({ data, date, editable }: { data: DaySchedule; date: string; editable: boolean }) {
  const lessonsAt = (lessons: Lesson[], period: Period) =>
    lessons.filter((lesson) => lesson.period.start_time < period.end_time && lesson.period.end_time > period.start_time);
  const busyDay = data.items.some((row) => row.lessons.length > 0);

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
            {data.items.map(({ room, lessons }) => (
              <tr key={room.id} className="[&:not(:last-child)>*]:border-b [&>*]:border-line">
                <th scope="row" className="sticky left-0 z-10 bg-white px-6 py-3 align-middle font-normal">
                  <span className="block font-bold whitespace-nowrap">Ауд. {room.number}</span>
                  <span className="block text-xs leading-[18px] whitespace-nowrap text-muted">
                    {room.building.name}
                  </span>
                </th>
                {data.periods.map((period) => {
                  const entries = lessonsAt(lessons, period);
                  const place = `Ауд. ${room.number}, ${periodTime(period)}`;
                  return (
                    <td key={period.id} className="h-[76px] px-2 py-2 align-top last:pr-6">
                      {entries.length > 0 ? (
                        <div className="space-y-2">
                          {entries.map((lesson) => editable ? (
                            <Link key={lesson.id}
                              to={`/schedule/${encodeURIComponent(lesson.id)}/edit?date=${date}`}
                              aria-label={`Изменить занятие: ${lesson.subject}, ${place}`}
                              className={cellLink}>
                              <LessonCell lesson={lesson} />
                            </Link>
                          ) : <LessonCell key={lesson.id} lesson={lesson} />)}
                        </div>
                      ) : editable ? (
                        <Link
                          to={`/schedule/new?date=${date}&room=${encodeURIComponent(room.id)}&period=${encodeURIComponent(period.id)}`}
                          aria-label={`Добавить занятие: ${place}`}
                          className={cellLink}
                        >
                          <FreeCell />
                        </Link>
                      ) : <FreeCell />}
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
  const loadSchedule = useCallback((signal: AbortSignal) => scheduleApi.schedule(date, signal), [date]);
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
          ) : result.data.items.length === 0 ? (
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
