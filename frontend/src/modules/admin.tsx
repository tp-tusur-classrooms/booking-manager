import { useCallback, type ReactNode } from 'react';
import { Link, Route, Routes, useLocation, useParams } from 'react-router';
import { classroomsApi, requestStatus } from './classrooms/api';
import { useRequest } from './classrooms/use-request';

const panel = 'rounded-2xl border border-[#e4e4ea] bg-white p-6';
const button = 'inline-flex rounded-[10px] bg-[#6952b3] px-[18px] py-3 text-sm font-medium text-white hover:bg-[#574198]';

function RequestFailure({ children, retry }: { children: ReactNode; retry: () => void }) {
  return (
    <div role="alert">
      <p>{children}</p>
      <button type="button" onClick={retry} className="mt-3 cursor-pointer font-medium text-[#6952b3] underline">
        Повторить запрос
      </button>
    </div>
  );
}

function ClassroomList() {
  const { state } = useLocation();
  const { result, retry } = useRequest(classroomsApi.list);

  return (
    <>
      <div className="mb-8 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-[32px] leading-tight font-bold">Управление аудиториями</h1>
          <p className="mt-2 text-sm text-[#626674]">Каталог помещений и доступность для бронирования.</p>
        </div>
        <Link to="new" className={button}>Добавить аудиторию</Link>
      </div>
      {state?.created && (
        <p role="status" className="mb-6 rounded-xl bg-[#e7f3ed] px-5 py-4 text-[#246447]">
          Аудитория добавлена и опубликована
        </p>
      )}
      <section aria-label="Список аудиторий" className={panel}>
        {result.status === 'loading' && <p role="status">Загрузка аудиторий…</p>}
        {result.status === 'error' && <RequestFailure retry={retry}>Не удалось загрузить аудитории.</RequestFailure>}
        {result.status === 'ready' && (result.data.length === 0 ? (
          <p>Список пока пуст. Добавьте первую аудиторию.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[680px] text-left text-sm">
              <thead className="border-b border-[#e4e4ea] text-xs text-[#626674]">
                <tr>
                  {['Аудитория', 'Расположение', 'Мест', 'Оборудование', 'Действия'].map((label) => (
                    <th key={label} scope="col" className="py-4 pr-4 font-medium">{label}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#e4e4ea]">
                {result.data.map((room) => (
                  <tr key={room.id}>
                    <th scope="row" className="py-5 pr-4 font-medium">Ауд. {room.number}</th>
                    <td className="pr-4">Корпус {room.building} · {room.floor} этаж</td>
                    <td className="pr-4">{room.capacity}</td>
                    <td className="pr-4">{room.equipment.join(', ') || 'Не указано'}</td>
                    <td className="py-5">
                      <Link to={encodeURIComponent(room.id)} aria-label={`Посмотреть аудиторию ${room.number}`}
                        className="inline-flex rounded-[10px] border border-[#e4e4ea] px-[18px] py-2.5 hover:bg-[#f7f7f9]">
                        Посмотреть
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}
      </section>
    </>
  );
}

function ClassroomDetails() {
  const { id = '' } = useParams();
  const load = useCallback((signal: AbortSignal) => classroomsApi.get(id, signal), [id]);
  const { result, retry } = useRequest(load);

  return (
    <>
      <Link to="/admin" className="mb-6 inline-block text-sm font-medium text-[#6952b3]">← К списку аудиторий</Link>
      <section className={panel}>
        {result.status === 'loading' && <p role="status">Загрузка аудитории…</p>}
        {result.status === 'error' && (requestStatus(result.error) === 404
          ? <p role="alert">Аудитория не найдена.</p>
          : <RequestFailure retry={retry}>Не удалось загрузить аудиторию.</RequestFailure>)}
        {result.status === 'ready' && (
          <div className="grid gap-6 md:grid-cols-2">
            <div>
              <h1 className="mb-5 text-[32px] font-bold">Аудитория {result.data.number}</h1>
              <dl className="grid gap-4 text-sm">
                <div><dt className="text-[#626674]">Расположение</dt><dd>Корпус {result.data.building} · {result.data.floor} этаж</dd></div>
                <div><dt className="text-[#626674]">Вместимость</dt><dd>{result.data.capacity}</dd></div>
                <div><dt className="text-[#626674]">Оборудование</dt><dd>{result.data.equipment.join(', ') || 'Не указано'}</dd></div>
                {result.data.description && <div><dt className="text-[#626674]">Описание</dt><dd>{result.data.description}</dd></div>}
              </dl>
            </div>
            {result.data.photo_url && <img className="w-full rounded-xl object-cover" src={result.data.photo_url} alt={`Аудитория ${result.data.number}`} />}
          </div>
        )}
      </section>
    </>
  );
}

export function AdminPage() {
  const { result, retry } = useRequest(classroomsApi.profile);

  if (result.status === 'loading') return <p role="status">Проверяем доступ…</p>;
  if (result.status === 'error') {
    const status = requestStatus(result.error);
    if (status === 401) return <p role="alert">Войдите в систему для доступа к управлению.</p>;
    if (status === 403) return <p role="alert">Управление доступно только администраторам.</p>;
    return <RequestFailure retry={retry}>Не удалось проверить доступ.</RequestFailure>;
  }
  if (result.data.role !== 'admin') return <p role="alert">Управление доступно только администраторам.</p>;

  return (
    <Routes>
      <Route index element={<ClassroomList />} />
      <Route path="new" element={<p>Форма добавления пока недоступна. <Link to="/admin" className="underline">К списку</Link></p>} />
      <Route path=":id" element={<ClassroomDetails />} />
    </Routes>
  );
}
