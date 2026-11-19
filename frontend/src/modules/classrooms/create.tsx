import { useEffect, useRef, useState, type FormEvent, type ReactNode } from 'react';
import { Link, useNavigate } from 'react-router';
import { requestStatus } from './api';
import { createClassroom, getClassroomOptions, publishClassroom, uploadClassroomPhoto, validationDetails } from './create-api';
import { useRequest } from './use-request';

const fields = ['number', 'building', 'floor', 'capacity', 'equipment', 'description', 'photo'] as const;
type FieldName = typeof fields[number];
type Errors = Partial<Record<FieldName, string>>;
const input = 'mt-2 min-h-12 w-full rounded-[10px] border border-[#dfe0e7] bg-white px-3 py-2 text-[#242529] outline-none focus:border-[#6952b3] aria-invalid:border-red-600';
const panel = 'rounded-2xl border border-[#e4e4ea] bg-white p-6 sm:p-8';

function Field({ name, label, errors, children }: {
  name: FieldName;
  label: string;
  errors: Errors;
  children: ReactNode;
}) {
  return (
    <div>
      <label htmlFor={name} className="block text-sm text-[#626674]">{label}</label>
      {children}
      {errors[name] && <p id={`${name}-error`} className="mt-1.5 text-sm text-red-700">{errors[name]}</p>}
    </div>
  );
}

function photoError(file: File) {
  if (!['image/jpeg', 'image/png'].includes(file.type)) return 'Выберите файл JPG или PNG.';
  if (file.size === 0 || file.size > 10 * 1024 * 1024) return 'Выберите непустой файл размером до 10 МБ.';
}

export function ClassroomCreate() {
  const navigate = useNavigate();
  const { result, retry } = useRequest(getClassroomOptions);
  const [errors, setErrors] = useState<Errors>({});
  const [message, setMessage] = useState('');
  const [photo, setPhoto] = useState<File | null>(null);
  const [preview, setPreview] = useState('');
  const [pending, setPending] = useState(false);
  const [draftId, setDraftId] = useState<string>();
  const [photoUploaded, setPhotoUploaded] = useState(false);
  const submitting = useRef(false);
  const active = useRef(false);
  const fileInput = useRef<HTMLInputElement>(null);

  useEffect(() => {
    active.current = true;
    return () => { active.current = false; };
  }, []);

  useEffect(() => () => {
    if (preview) URL.revokeObjectURL(preview);
  }, [preview]);

  function selectPhoto(file: File | null) {
    const error = file ? photoError(file) : undefined;
    setErrors((previous) => ({ ...previous, photo: error }));
    setPhoto(error ? null : file);
    setPreview(file && !error ? URL.createObjectURL(file) : '');
    if (fileInput.current && (!file || error)) fileInput.current.value = '';
  }

  function props(name: FieldName) {
    return {
      id: name, name, className: input,
      'aria-invalid': Boolean(errors[name]),
      'aria-describedby': errors[name] ? `${name}-error` : undefined,
      onChange: () => setErrors((previous) => ({ ...previous, [name]: undefined })),
    };
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (submitting.current || result.status !== 'ready') return;

    const form = new FormData(event.currentTarget);
    const read = (name: FieldName) => String(form.get(name) ?? '').trim();
    const input = {
      number: read('number'),
      building_id: read('building'),
      floor: Number(read('floor')),
      capacity: Number(read('capacity')),
      equipment_ids: form.getAll('equipment').map(String),
      description: read('description') || null,
    };
    const next: Errors = {};
    if (!draftId) {
      if (!input.number) next.number = 'Введите номер аудитории.';
      else if (Array.from(input.number).length > 20) next.number = 'Введите не больше 20 символов.';
      if (!input.building_id) next.building = 'Выберите корпус.';
      if (!read('floor') || !Number.isInteger(input.floor) || input.floor < -5 || input.floor > 50) {
        next.floor = 'Укажите целое число от −5 до 50.';
      }
      if (!Number.isInteger(input.capacity) || input.capacity < 1 || input.capacity > 1000) {
        next.capacity = 'Укажите целое число от 1 до 1000.';
      }
      if (input.description && Array.from(input.description).length > 1000) {
        next.description = 'Введите не больше 1000 символов.';
      }
    }
    if (errors.photo && !photo) next.photo = errors.photo;
    setErrors(next);
    setMessage('');
    if (Object.keys(next).length) return;

    submitting.current = true;
    setPending(true);
    let stage: 'create' | 'photo' | 'publish' = 'create';
    try {
      const id = draftId ?? await createClassroom(input);
      setDraftId(id);
      if (photo && !photoUploaded) {
        stage = 'photo';
        await uploadClassroomPhoto(id, photo);
        setPhotoUploaded(true);
      }
      stage = 'publish';
      await publishClassroom(id);
      if (active.current) void navigate('/admin', { replace: true, state: { created: true } });
    } catch (error) {
      const status = requestStatus(error);
      if (stage === 'create' && status === 409) {
        setErrors({ number: 'Аудитория с таким номером уже есть в этом корпусе.' });
      } else {
        const serverErrors: Errors = {};
        const fieldAliases: Record<string, FieldName> = {
          building_id: 'building', equipment_ids: 'equipment', file: 'photo',
        };
        for (const issue of validationDetails(error)) {
          const key = fields.find((name) => name === (fieldAliases[issue.field] ?? issue.field));
          if (key && issue.message) serverErrors[key] = issue.message;
        }
        setErrors(serverErrors);
        if (!Object.keys(serverErrors).length) {
          const messages = {
            create: 'Не удалось создать аудиторию. Повторите отправку.',
            photo: 'Черновик сохранён. Не удалось загрузить фото. Повторите отправку.',
            publish: 'Черновик сохранён. Не удалось опубликовать аудиторию. Повторите отправку.',
          };
          setMessage(status === 401 || status === 403
            ? 'Для публикации нужен доступ администратора.'
            : messages[stage]);
        }
      }
    } finally {
      submitting.current = false;
      setPending(false);
    }
  }

  return (
    <>
      <h1 className="text-[32px] leading-tight font-bold">Добавить аудиторию</h1>
      <p className="mt-2 mb-8 text-sm text-[#626674]">Укажите характеристики помещения для каталога.</p>
      {result.status === 'loading' && <p role="status">Загрузка справочников…</p>}
      {result.status === 'error' && (
        <p role="alert" className="mb-5">
          Не удалось загрузить справочники.{' '}
          <button type="button" onClick={retry} className="text-[#6952b3] underline">Повторить запрос</button>
        </p>
      )}
      <form noValidate onSubmit={(event) => void submit(event)} aria-busy={pending}
        className="grid items-start gap-8 lg:grid-cols-[2.08fr_1fr]">
        <section className={panel} aria-labelledby="room-info">
          <h2 id="room-info" className="mb-6 text-[22px] font-bold">Основная информация</h2>
          <fieldset disabled={pending || Boolean(draftId)} className="space-y-6">
            <div className="grid gap-6 sm:grid-cols-3">
              <Field name="number" label="Номер аудитории" errors={errors}>
                <input {...props('number')} required />
              </Field>
              <Field name="building" label="Корпус" errors={errors}>
                <select {...props('building')} defaultValue="" required>
                  <option value="">Выберите корпус</option>
                  {result.status === 'ready' && result.data.buildings.map(({ id, name }) => (
                    <option key={id} value={id}>{name}</option>
                  ))}
                </select>
              </Field>
              <Field name="floor" label="Этаж" errors={errors}>
                <input {...props('floor')} type="number" step="1" required />
              </Field>
            </div>
            <Field name="capacity" label="Вместимость" errors={errors}>
              <input {...props('capacity')} type="number" step="1" min="1" required />
            </Field>
            <fieldset className="border-t border-[#e4e4ea] pt-6" aria-labelledby="equipment-title"
              aria-describedby={errors.equipment ? 'equipment-error' : undefined}>
              <h3 id="equipment-title" className="mb-4 text-lg font-bold">Оборудование</h3>
              <div className="grid gap-x-6 gap-y-4 sm:grid-cols-2">
                {result.status === 'ready' && result.data.equipment.map(({ id, name }) => (
                  <label key={id} className="flex items-center gap-3 text-sm">
                    <input type="checkbox" name="equipment" value={id} className="size-4 accent-[#6952b3]" />
                    {name}
                  </label>
                ))}
              </div>
              {errors.equipment && <p id="equipment-error" className="mt-2 text-sm text-red-700">{errors.equipment}</p>}
            </fieldset>
            <Field name="description" label="Описание" errors={errors}>
              <textarea {...props('description')} rows={2} className={`${input} resize-y`} />
            </Field>
          </fieldset>
          {draftId && !pending && <p className="mt-4 text-sm">Аудитория сохранена как черновик.</p>}
          {message && <p role="alert" className="mt-4 text-sm text-red-700">{message}</p>}
          <div className="mt-6 flex items-center gap-3">
            <button type="submit" disabled={pending || result.status !== 'ready'}
              className="rounded-[10px] bg-[#6952b3] px-[18px] py-3 text-sm text-white hover:bg-[#574198] disabled:opacity-60">
              {pending ? 'Сохраняем…' : draftId ? 'Продолжить публикацию' : 'Добавить аудиторию'}
            </button>
            {pending ? (
              <button type="button" disabled className="rounded-[10px] border border-[#e4e4ea] px-5 py-3 text-sm opacity-60">Отмена</button>
            ) : (
              <Link to="/admin" className="rounded-[10px] border border-[#e4e4ea] px-5 py-3 text-sm hover:bg-[#f7f7f9]">{draftId ? 'К списку' : 'Отмена'}</Link>
            )}
          </div>
        </section>
        <section className={`${panel} min-h-[368px]`} aria-labelledby="photo-title">
          <h2 id="photo-title" className="mb-6 text-lg font-bold">Фотография аудитории</h2>
          <div className="rounded-2xl border border-[#e4e4ea] bg-[#f7f7f9] p-6 text-center">
            {preview && <img src={preview} alt="Предпросмотр фотографии аудитории" className="mb-4 max-h-56 w-full rounded-lg object-contain" />}
            <p className="text-sm">{photo ? photo.name : 'Добавьте фотографию'}</p>
            <p id="photo-format" className="my-3 text-xs text-[#626674]">JPG или PNG · до 10 МБ</p>
            <input ref={fileInput} type="file" id="photo" name="photo" accept="image/jpeg,image/png"
              className="peer sr-only" disabled={pending || photoUploaded} aria-invalid={Boolean(errors.photo)}
              aria-describedby={errors.photo ? 'photo-format photo-error' : 'photo-format'}
              onChange={(event) => selectPhoto(event.currentTarget.files?.[0] ?? null)} />
            {!photoUploaded && <label htmlFor="photo" className="inline-flex w-full max-w-60 cursor-pointer justify-center rounded-[10px] border border-[#e4e4ea] bg-white px-5 py-3 text-sm peer-focus-visible:outline-2 peer-focus-visible:outline-[#6952b3]">
              {photo ? 'Заменить файл' : 'Выбрать файл'}
            </label>}
            {!photoUploaded && (photo || errors.photo) && (
              <button type="button" disabled={pending} onClick={() => selectPhoto(null)}
                className="mx-auto mt-3 block text-sm text-[#6952b3] underline">{photo ? 'Удалить фото' : 'Продолжить без фото'}</button>
            )}
            {errors.photo && <p id="photo-error" role="alert" className="mt-3 text-sm text-red-700">{errors.photo}</p>}
          </div>
        </section>
      </form>
    </>
  );
}
