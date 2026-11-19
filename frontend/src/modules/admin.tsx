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
      <div className="flex flex-col gap-2">
        <h1 className="text-[32px] leading-10 font-bold">Управление аудиториями</h1>
        <p className="text-sm leading-[22px] text-muted">Каталог помещений и доступность для бронирования.</p>
      </div>
      <section
        aria-labelledby="api-title"
        className="mt-8 flex flex-col items-start gap-6 rounded-2xl border border-line bg-white p-8"
      >
        <h2 id="api-title" className="text-[22px] leading-[30px] font-bold">
          Состояние API
        </h2>
        <p role="status" className="text-sm leading-[22px] text-muted">
          {statusText[status]}
        </p>
        <button
          type="button"
          disabled={status === 'checking'}
          onClick={() => void check()}
          className="h-11 cursor-pointer rounded-[10px] bg-accent px-4 text-sm leading-5 text-white outline-accent focus-visible:outline-2 focus-visible:outline-offset-2 disabled:cursor-default disabled:bg-line disabled:text-muted"
        >
          Проверить подключение
        </button>
      </section>
    </>
  );
}
