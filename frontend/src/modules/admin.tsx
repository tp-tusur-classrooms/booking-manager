import { useApiStatus } from '../api-status';

const statusText = {
  idle: 'Подключение ещё не проверено.',
  checking: 'Проверяем подключение…',
  online: 'API отвечает.',
  offline: 'Не удалось подключиться к API.',
};

export function AdminPage() {
  const status = useApiStatus((state) => state.status);
  const check = useApiStatus((state) => state.check);

  return (
    <>
      <h1 className="text-3xl font-semibold">Администрирование</h1>
      <section aria-labelledby="api-title" className="mt-6 rounded-lg border border-slate-200 bg-white p-5">
        <h2 id="api-title" className="text-lg font-semibold">Состояние API</h2>
        <p role="status" className="mt-2 text-slate-600">
          {statusText[status]}
        </p>
        <button
          type="button"
          disabled={status === 'checking'}
          onClick={() => void check()}
          className="mt-4 rounded-md bg-blue-700 px-4 py-2 font-medium text-white hover:bg-blue-800 disabled:opacity-60"
        >
          Проверить подключение
        </button>
      </section>
    </>
  );
}
