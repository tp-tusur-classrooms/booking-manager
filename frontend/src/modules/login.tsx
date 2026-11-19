import { isAxiosError } from 'axios';
import { useState, type FormEvent, type InputHTMLAttributes } from 'react';
import { Navigate, useLocation } from 'react-router';
import classroom from '../assets/classroom.png';
import logo from '../assets/logo.svg';
import { useSession, type Role } from '../session';

type FieldName = 'login' | 'password';

interface Notice {
  tone: 'error' | 'warning';
  title: string;
  text: string;
  fields?: FieldName[];
}

const homeByRole: Record<Role, string> = { user: '/', admin: '/admin' };

const expiredNotice: Notice = {
  tone: 'warning',
  title: 'Сессия истекла',
  text: 'Войдите снова, чтобы продолжить.',
};

function emptyFieldsNotice(login: string, password: string): Notice | null {
  if (!login && !password) {
    return {
      tone: 'error',
      title: 'Введите логин и пароль',
      text: 'Поля логина и пароля обязательны для входа.',
      fields: ['login', 'password'],
    };
  }
  if (!login) {
    return { tone: 'error', title: 'Введите логин', text: 'Поле логина обязательно для входа.', fields: ['login'] };
  }
  if (!password) {
    return { tone: 'error', title: 'Введите пароль', text: 'Поле пароля обязательно для входа.', fields: ['password'] };
  }
  return null;
}

function failureNotice(error: unknown): Notice {
  const status = isAxiosError(error) ? error.response?.status : undefined;
  if (status === 400 || status === 401) {
    return {
      tone: 'error',
      title: 'Не удалось войти',
      text: 'Проверьте логин и пароль.',
      fields: ['login', 'password'],
    };
  }
  return { tone: 'error', title: 'Не удалось войти', text: 'Сервер недоступен. Попробуйте позже.' };
}

function NoticeBox({ notice }: { notice: Notice }) {
  const background = notice.tone === 'error' ? 'bg-error-soft' : 'bg-warning-soft';
  return (
    <div role="alert" className={`flex flex-col gap-1 rounded-xl border border-line p-4 ${background}`}>
      <p className="text-sm leading-5 text-ink">{notice.title}</p>
      <p className="text-xs leading-[18px] text-muted">{notice.text}</p>
    </div>
  );
}

function Field({ label, ...input }: { label: string } & InputHTMLAttributes<HTMLInputElement>) {
  return (
    <label className="flex flex-col gap-2">
      <span className="text-sm leading-5 text-muted">{label}</span>
      <input
        {...input}
        className="h-12 rounded-[10px] border border-line bg-white p-3 text-sm leading-[22px] text-ink outline-none focus:border-accent focus:ring-3 focus:ring-accent/20"
      />
    </label>
  );
}

export function LoginPage() {
  const status = useSession((state) => state.status);
  const user = useSession((state) => state.user);
  const login = useSession((state) => state.login);
  const location = useLocation();
  const [values, setValues] = useState({ login: '', password: '' });
  const [notice, setNotice] = useState<Notice | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (status === 'authenticated' && user) {
    const from = (location.state as { from?: string } | null)?.from;
    return <Navigate to={from ?? homeByRole[user.role]} replace />;
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const loginValue = values.login.trim();
    const empty = emptyFieldsNotice(loginValue, values.password);
    if (empty) {
      setNotice(empty);
      return;
    }

    setSubmitting(true);
    setNotice(null);
    try {
      await login(loginValue, values.password);
    } catch (error) {
      setNotice(failureNotice(error));
      setSubmitting(false);
    }
  }

  const shown = notice ?? (status === 'expired' ? expiredNotice : null);
  const invalid = (field: FieldName) => shown?.fields?.includes(field) || undefined;

  return (
    <div className="mx-auto flex min-h-screen w-full max-w-[1440px] flex-col gap-16 bg-white p-6 text-ink lg:p-16">
      <div className="flex items-center justify-center gap-3 lg:justify-start">
        <img src={logo} alt="" width={32} height={40} />
        <p className="text-[22px] leading-[30px] font-bold">Аудитории</p>
      </div>
      <div className="flex justify-center gap-24 lg:justify-start">
        <section className="hidden max-w-[656px] flex-1 flex-col gap-6 lg:flex">
          <p className="text-[32px] leading-10 font-bold">
            Место для ваших
            <br />
            больших идей.
          </p>
          <p className="max-w-[560px] text-sm leading-[22px] text-muted">
            Найдите свободную аудиторию и запланируйте следующее занятие.
          </p>
          <img src={classroom} alt="" className="h-80 w-full rounded-xl bg-illustration object-cover" />
        </section>
        <form noValidate onSubmit={submit} className="flex w-full max-w-[464px] shrink-0 flex-col gap-6">
          <h1 className="text-[32px] leading-10 font-bold">Вход в систему</h1>
          <p className="text-sm leading-[22px] text-muted">Используйте учётную запись университета.</p>
          {shown && <NoticeBox notice={shown} />}
          <Field
            label="Логин"
            name="login"
            autoComplete="username"
            aria-invalid={invalid('login')}
            value={values.login}
            onChange={(event) => setValues({ ...values, login: event.target.value })}
          />
          <Field
            label="Пароль"
            name="password"
            type="password"
            autoComplete="current-password"
            aria-invalid={invalid('password')}
            value={values.password}
            onChange={(event) => setValues({ ...values, password: event.target.value })}
          />
          <button
            type="submit"
            disabled={submitting}
            className="h-11 cursor-pointer rounded-[10px] bg-accent px-4 py-3 text-sm leading-5 text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent disabled:cursor-default disabled:bg-line disabled:text-muted"
          >
            Войти в систему
          </button>
          <p className="text-xs leading-[18px] text-muted">Не получается войти? Обратитесь к администратору.</p>
        </form>
      </div>
    </div>
  );
}
