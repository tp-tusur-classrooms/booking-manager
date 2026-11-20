import { isAxiosError } from 'axios';
import { useCallback, useState, type FormEvent } from 'react';
import { Link, useNavigate, useParams, useSearchParams } from 'react-router';
import type { ApiError } from '../../api';
import { ConfirmDialog, FormField, inputClass, Notice, primaryButton, secondaryButton, StatePanel } from '../../ui';
import { classroomsApi, requestStatus, type Classroom } from '../classrooms/api';
import { useRequest } from '../classrooms/use-request';
import { periodTime, scheduleApi, type Lesson, type LessonWrite, type Period } from './api';
import { formatDate, isDate } from './dates';

type Field = 'room_id' | 'period_id' | 'date' | 'subject' | 'group' | 'teacher';

interface Values {
  room_id: string;
  period_id: string;
  date: string;
  subject: string;
  group: string;
  teacher: string;
}

type Errors = Partial<Record<Field, string>>;

interface Problem {
  title: string;
  text: string;
}

interface FormData {
  rooms: Classroom[];
  periods: Period[];
  lesson?: Lesson;
}

function initialValues(data: FormData, params: URLSearchParams): Values {
  const { lesson } = data;
  if (lesson) {
    return {
      room_id: lesson.room.id,
      period_id: lesson.period.id,
      date: lesson.date,
      subject: lesson.subject ?? '',
      group: lesson.group ?? '',
      teacher: lesson.teacher ?? '',
    };
  }
  const date = params.get('date');
  const room = params.get('room') ?? '';
  const period = params.get('period') ?? '';
  return {
    room_id: data.rooms.some((item) => item.id === room) ? room : '',
    period_id: data.periods.some((item) => item.id === period) ? period : '',
    date: isDate(date) ? date : '',
    subject: '',
    group: '',
    teacher: '',
  };
}

function validate(values: Values): Errors {
  const errors: Errors = {};
  if (!values.room_id) errors.room_id = 'Выберите аудиторию';
  if (!values.period_id) errors.period_id = 'Выберите учебный период';
  if (!isDate(values.date)) errors.date = 'Укажите дату занятия';
  if (!values.subject.trim()) errors.subject = 'Введите название занятия';
  return errors;
}

function toPayload(values: Values): LessonWrite {
  const text = (value: string) => value.trim() || null;
  return {
    room_id: values.room_id,
    period_id: values.period_id,
    date: values.date,
    subject: values.subject.trim(),
    group: text(values.group),
    teacher: text(values.teacher),
  };
}

function describeConflict(lesson: Lesson) {
  const name = lesson.subject ? `«${lesson.subject}»` : 'без названия';
  return `Пересекается с занятием ${name}: ауд. ${lesson.room.number}, ${formatDate(lesson.date)}, ${periodTime(lesson.period)}.`;
}

function failure(error: unknown): { errors: Errors; problem: Problem } {
  if (!isAxiosError<ApiError & { conflicts?: Lesson[] }>(error) || !error.response) {
    return { errors: {}, problem: { title: 'Не удалось сохранить занятие', text: 'Сервер недоступен. Проверьте подключение и попробуйте снова.' } };
  }
  const { status, data } = error.response;
  if (status === 409) {
    const conflict = data?.conflicts?.[0];
    return {
      errors: {},
      problem: {
        title: 'Аудитория уже занята в это время',
        text: `${conflict ? `${describeConflict(conflict)} ` : ''}Выберите другую аудиторию, период или дату.`,
      },
    };
  }
  if (status === 400 && data?.errors?.length) {
    const errors: Errors = {};
    for (const item of data.errors) errors[item.field as Field] = item.message;
    return { errors, problem: { title: 'Проверьте заполнение полей', text: 'Исправьте отмеченные поля и сохраните снова.' } };
  }
  if (status === 404) {
    return { errors: {}, problem: { title: 'Занятие не найдено', text: 'Возможно, его уже удалили. Вернитесь к расписанию.' } };
  }
  return { errors: {}, problem: { title: 'Не удалось сохранить занятие', text: data?.message ?? 'Попробуйте ещё раз.' } };
}

const longDay = new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' });

function dayText(date: string) {
  return longDay.format(new Date(`${date}T00:00:00Z`));
}

function DeleteLesson({ lesson, backDate }: { lesson: Lesson; backDate: string | null }) {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);

  async function remove() {
    setDeleting(true);
    setProblem(null);
    try {
      await scheduleApi.remove(lesson.id);
      navigate(`/schedule?date=${backDate ?? lesson.date}`);
    } catch (error) {
      if (requestStatus(error) === 404) {
        navigate(`/schedule?date=${backDate ?? lesson.date}`);
        return;
      }
      setProblem(isAxiosError(error) && error.response ? 'Сервер не смог удалить занятие. Попробуйте ещё раз.' : 'Сервер недоступен. Проверьте подключение и попробуйте снова.');
      setDeleting(false);
    }
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="h-11 cursor-pointer rounded-[10px] px-4 text-sm leading-5 text-danger outline-danger hover:bg-error-soft focus-visible:outline-2 focus-visible:outline-offset-2 sm:ml-auto"
      >
        Удалить занятие
      </button>
      <ConfirmDialog
        open={open}
        title="Удалить занятие?"
        cancelLabel="Оставить занятие"
        confirmLabel={deleting ? 'Удаляем…' : 'Удалить занятие'}
        busy={deleting}
        onCancel={() => {
          setOpen(false);
          setProblem(null);
        }}
        onConfirm={() => void remove()}
      >
        <p className="text-sm leading-5 font-bold">{lesson.subject ?? 'Учебное занятие'}</p>
        <p className="mt-2 text-sm leading-[22px] text-muted">
          Аудитория {lesson.room.number} · {lesson.room.building.name}
          <br />
          {dayText(lesson.date)} · {periodTime(lesson.period)}
        </p>
        <p className="mt-6 border-t border-line pt-6 text-sm leading-[22px] text-muted">
          Занятие исчезнет из расписания на эту дату. Вернуть его можно будет только добавив заново.
        </p>
        {problem && (
          <div className="mt-6">
            <Notice title="Не удалось удалить занятие" text={problem} />
          </div>
        )}
      </ConfirmDialog>
    </>
  );
}

function LessonForm({ data, lessonId, backDate }: { data: FormData; lessonId?: string; backDate: string | null }) {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const [values, setValues] = useState(() => initialValues(data, params));
  const [errors, setErrors] = useState<Errors>({});
  const [problem, setProblem] = useState<Problem | null>(null);
  const [saving, setSaving] = useState(false);

  const back = `/schedule${backDate ? `?date=${backDate}` : ''}`;

  const change = (field: Field) => (event: { target: { value: string } }) => {
    setValues((current) => ({ ...current, [field]: event.target.value }));
    setErrors((current) => ({ ...current, [field]: undefined }));
  };

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const found = validate(values);
    setErrors(found);
    if (Object.keys(found).length > 0) {
      setProblem({ title: 'Проверьте заполнение полей', text: 'Исправьте отмеченные поля и сохраните снова.' });
      return;
    }
    setSaving(true);
    setProblem(null);
    try {
      const payload = toPayload(values);
      if (lessonId) await scheduleApi.update(lessonId, payload);
      else await scheduleApi.create(payload);
      navigate(`/schedule?date=${payload.date}`);
    } catch (error) {
      const result = failure(error);
      setErrors(result.errors);
      setProblem(result.problem);
      setSaving(false);
    }
  }

  return (
    <form noValidate onSubmit={submit} className="mt-8 flex max-w-[864px] flex-col gap-6 rounded-2xl border border-line bg-white p-6 sm:p-8">
      <h2 className="text-[22px] leading-[30px] font-bold">Детали занятия</h2>
      <div className="grid gap-6 sm:grid-cols-3">
        <FormField label="Аудитория" error={errors.room_id}>
          <select value={values.room_id} onChange={change('room_id')} className={inputClass}>
            <option value="">Выберите аудиторию</option>
            {data.rooms.map((room) => (
              <option key={room.id} value={room.id}>
                Ауд. {room.number} · {room.building.name}
              </option>
            ))}
          </select>
        </FormField>
        <FormField label="Учебный период" error={errors.period_id}>
          <select value={values.period_id} onChange={change('period_id')} className={inputClass}>
            <option value="">Выберите период</option>
            {data.periods.map((period) => (
              <option key={period.id} value={period.id}>
                {periodTime(period)}
              </option>
            ))}
          </select>
        </FormField>
        <FormField label="Дата занятия" error={errors.date}>
          <input type="date" value={values.date} onChange={change('date')} className={inputClass} />
        </FormField>
      </div>
      <FormField label="Название занятия" error={errors.subject}>
        <input value={values.subject} required maxLength={200} onChange={change('subject')} placeholder="Например, Технология программирования" className={inputClass} />
      </FormField>
      <div className="grid gap-6 sm:grid-cols-2">
        <FormField label="Группа" error={errors.group}>
          <input value={values.group} maxLength={200} onChange={change('group')} placeholder="Например, 432-1" className={inputClass} />
        </FormField>
        <FormField label="Преподаватель" error={errors.teacher}>
          <input value={values.teacher} maxLength={200} onChange={change('teacher')} placeholder="Например, Петров П. П." className={inputClass} />
        </FormField>
      </div>
      {problem && <Notice title={problem.title} text={problem.text} />}
      <div className="flex flex-wrap gap-3">
        <button type="submit" disabled={saving} className={primaryButton}>
          {saving ? 'Сохраняем…' : lessonId ? 'Сохранить изменения' : 'Добавить занятие'}
        </button>
        <Link to={back} className={secondaryButton}>
          Отмена
        </Link>
        {data.lesson && <DeleteLesson lesson={data.lesson} backDate={backDate} />}
      </div>
    </form>
  );
}

function LessonPage({ lessonId }: { lessonId?: string }) {
  const [params] = useSearchParams();
  const date = params.get('date');
  const backDate = isDate(date) ? date : null;
  const load = useCallback(
    async (signal: AbortSignal): Promise<FormData> => {
      const [rooms, periods, lesson] = await Promise.all([
        classroomsApi.list(signal),
        scheduleApi.periods(signal),
        lessonId ? scheduleApi.lesson(lessonId, signal) : Promise.resolve(undefined),
      ]);
      return { rooms, periods, lesson };
    },
    [lessonId],
  );
  const { result, retry } = useRequest(load);
  const back = `/schedule${backDate ? `?date=${backDate}` : ''}`;

  return (
    <>
      <h1 className="text-[32px] leading-10 font-bold">{lessonId ? 'Изменить занятие' : 'Добавить занятие'}</h1>
      <p className="mt-2 text-sm leading-[22px] text-muted">
        {backDate ? `Расписание на ${formatDate(backDate)}` : 'Одно занятие на выбранную дату и учебный период. Часовой пояс — Томск (UTC+7).'}
      </p>
      {result.status === 'loading' && (
        <div role="status" className="mt-8 h-[560px] max-w-[864px] rounded-2xl border border-line bg-white motion-safe:animate-pulse">
          <span className="sr-only">Загружаем форму</span>
        </div>
      )}
      {result.status === 'error' && (
        <div className="mt-8 max-w-[864px]">
          {requestStatus(result.error) === 404 || requestStatus(result.error) === 400 ? (
            <StatePanel title="Занятие не найдено" text="Возможно, его уже удалили.">
              <Link to={back} className={primaryButton}>
                К расписанию
              </Link>
            </StatePanel>
          ) : (
            <StatePanel alert title="Не удалось загрузить данные" text="Проверьте подключение к интернету и повторите попытку.">
              <button type="button" onClick={retry} className={primaryButton}>
                Повторить
              </button>
            </StatePanel>
          )}
        </div>
      )}
      {result.status === 'ready' && <LessonForm data={result.data} lessonId={lessonId} backDate={backDate} />}
    </>
  );
}

export function NewLessonRoute() {
  return <LessonPage />;
}

export function EditLessonRoute() {
  const { lessonId = '' } = useParams();
  return <LessonPage key={lessonId} lessonId={lessonId} />;
}
