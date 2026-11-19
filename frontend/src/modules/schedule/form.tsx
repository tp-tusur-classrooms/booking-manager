import { isAxiosError } from 'axios';
import { useCallback, useState, type FormEvent } from 'react';
import { Link, useNavigate, useParams, useSearchParams } from 'react-router';
import type { ApiError } from '../../api';
import { FormField, inputClass, Notice, primaryButton, secondaryButton, StatePanel } from '../../ui';
import { classroomsApi, requestStatus, type Classroom } from '../classrooms/api';
import { useRequest } from '../classrooms/use-request';
import { periodTime, scheduleApi, type Lesson, type LessonWrite, type Period, type WeekParity } from './api';
import { firstOccurrence, formatDate, occursOn, weekday } from './dates';

const weekdays = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье'];
const shortWeekdays = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс'];

const parities: { value: WeekParity; label: string }[] = [
  { value: 'every', label: 'Каждую неделю' },
  { value: 'odd', label: 'По нечётным неделям' },
  { value: 'even', label: 'По чётным неделям' },
];

type Field = 'room_id' | 'period_id' | 'weekday' | 'week_parity' | 'starts_on' | 'ends_on' | 'subject' | 'group' | 'teacher';

interface Values {
  room_id: string;
  period_id: string;
  weekday: string;
  week_parity: WeekParity;
  starts_on: string;
  ends_on: string;
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

function isDate(value: string | null): value is string {
  return value !== null && /^\d{4}-\d{2}-\d{2}$/.test(value) && !Number.isNaN(Date.parse(value));
}

function initialValues(data: FormData, params: URLSearchParams): Values {
  const { lesson } = data;
  if (lesson) {
    return {
      room_id: lesson.room.id,
      period_id: lesson.period.id,
      weekday: String(lesson.weekday),
      week_parity: lesson.week_parity,
      starts_on: lesson.starts_on,
      ends_on: lesson.ends_on,
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
    weekday: isDate(date) ? String(weekday(date)) : '',
    week_parity: 'every',
    starts_on: isDate(date) ? date : '',
    ends_on: isDate(date) ? date : '',
    subject: '',
    group: '',
    teacher: '',
  };
}

function validate(values: Values): Errors {
  const errors: Errors = {};
  if (!values.room_id) errors.room_id = 'Выберите аудиторию';
  if (!values.period_id) errors.period_id = 'Выберите учебный период';
  if (!values.weekday) errors.weekday = 'Выберите день недели';
  if (!values.starts_on) errors.starts_on = 'Укажите дату начала';
  if (!values.ends_on) errors.ends_on = 'Укажите дату окончания';
  else if (values.starts_on && values.ends_on < values.starts_on) {
    errors.ends_on = 'Дата окончания не может быть раньше даты начала';
  }
  if (Object.keys(errors).length === 0 && !firstOccurrence(toPayload(values))) {
    errors.weekday =
      values.week_parity === 'every'
        ? 'В выбранные даты нет такого дня недели'
        : 'В выбранные даты нет такого дня недели с нужной чётностью';
  }
  return errors;
}

function toPayload(values: Values): LessonWrite {
  const text = (value: string) => value.trim() || null;
  return {
    room_id: values.room_id,
    period_id: values.period_id,
    weekday: Number(values.weekday),
    week_parity: values.week_parity,
    starts_on: values.starts_on,
    ends_on: values.ends_on,
    subject: text(values.subject),
    group: text(values.group),
    teacher: text(values.teacher),
  };
}

function describeConflict(lesson: Lesson) {
  const parity = lesson.week_parity === 'every' ? '' : lesson.week_parity === 'odd' ? ', нечётные недели' : ', чётные недели';
  const name = lesson.subject ? `«${lesson.subject}»` : 'без названия';
  return `Пересекается с занятием ${name}: ауд. ${lesson.room.number}, ${shortWeekdays[lesson.weekday - 1]}, ${periodTime(lesson.period)}${parity}.`;
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
        text: `${conflict ? `${describeConflict(conflict)} ` : ''}Выберите другую аудиторию, период или даты.`,
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
      const target = backDate && occursOn(payload, backDate) ? backDate : (firstOccurrence(payload) ?? payload.starts_on);
      navigate(`/schedule?date=${target}`);
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
                {room.status === 'draft' ? ' · черновик' : ''}
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
        <FormField label="День недели" error={errors.weekday}>
          <select value={values.weekday} onChange={change('weekday')} className={inputClass}>
            <option value="">Выберите день</option>
            {weekdays.map((name, index) => (
              <option key={name} value={index + 1}>
                {name}
              </option>
            ))}
          </select>
        </FormField>
        <FormField label="Повторение" error={errors.week_parity}>
          <select value={values.week_parity} onChange={change('week_parity')} className={inputClass}>
            {parities.map((parity) => (
              <option key={parity.value} value={parity.value}>
                {parity.label}
              </option>
            ))}
          </select>
        </FormField>
        <FormField label="Действует с" error={errors.starts_on}>
          <input type="date" value={values.starts_on} onChange={change('starts_on')} className={inputClass} />
        </FormField>
        <FormField label="Действует по" error={errors.ends_on}>
          <input type="date" value={values.ends_on} min={values.starts_on || undefined} onChange={change('ends_on')} className={inputClass} />
        </FormField>
      </div>
      <FormField label="Предмет" error={errors.subject}>
        <input value={values.subject} maxLength={200} onChange={change('subject')} placeholder="Например, Технология программирования" className={inputClass} />
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
        {backDate ? `Расписание на ${formatDate(backDate)}` : 'Занятие повторяется в выбранный день недели и период.'}
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
