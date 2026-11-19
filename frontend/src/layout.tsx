import { Link, Navigate, NavLink, Outlet, useLocation } from 'react-router';
import logo from './assets/logo.svg';
import bell from './assets/notifications.svg';
import { homeByRole, useSession, type Role } from './session';

const navByRole: Record<Role, { to: string; label: string }[]> = {
  user: [{ to: '/', label: 'Найти аудиторию' }],
  admin: [{ to: '/admin', label: 'Управление' }],
};

function nameLines(name: string) {
  const [first = '', ...rest] = name.trim().split(/\s+/);
  return [first, rest.join(' ')];
}

function initials(name: string) {
  return name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((word) => word[0])
    .join('')
    .toUpperCase();
}

export function RequireAuth() {
  const status = useSession((state) => state.status);
  const location = useLocation();

  if (status === 'loading') return null;
  if (status !== 'authenticated') {
    const state = status === 'expired' ? { from: location.pathname } : undefined;
    return <Navigate to="/login" replace state={state} />;
  }
  return <Outlet />;
}

export function RequireRole({ role }: { role: Role }) {
  const user = useSession((state) => state.user);

  if (!user) return null;
  if (user.role !== role) return <Navigate to={homeByRole[user.role]} replace />;
  return <Outlet />;
}

function Header() {
  const user = useSession((state) => state.user);
  const logout = useSession((state) => state.logout);

  if (!user) return null;
  const [firstLine, secondLine] = nameLines(user.name);

  return (
    <header className="border-b border-nav-line bg-white">
      <div className="mx-auto flex h-[87px] w-full max-w-[1440px] items-stretch px-6 lg:px-16">
        <Link
          to={homeByRole[user.role]}
          className="flex shrink-0 items-center gap-2.5 rounded-[10px] outline-accent focus-visible:outline-2 lg:w-[354px]"
        >
          <img src={logo} alt="" width={32} height={40} />
          <span className="hidden text-xl font-bold text-black sm:inline">Аудитории</span>
        </Link>
        <nav aria-label="Основная навигация" className="ml-6 flex gap-16 lg:ml-0">
          {navByRole[user.role].map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className="relative flex items-center text-sm text-black outline-accent focus-visible:outline-2 aria-[current=page]:font-bold"
            >
              {({ isActive }) => (
                <>
                  {item.label}
                  {isActive && <span className="absolute inset-x-0 -bottom-px h-[3px] rounded-[1px] bg-accent" />}
                </>
              )}
            </NavLink>
          ))}
        </nav>
        <div className="ml-auto flex items-center">
          {user.role === 'admin' && (
            <span className="mr-4 hidden border-r border-nav-line pr-4 sm:block">
              <img src={bell} alt="Уведомления" />
            </span>
          )}
          <span
            aria-hidden="true"
            className="flex size-10 shrink-0 items-center justify-center rounded-full bg-avatar text-[13px] font-bold text-black"
          >
            {initials(user.name)}
          </span>
          <p className="ml-3 hidden max-w-40 flex-col gap-1 text-[13px] leading-4 text-black sm:flex">
            <span className="truncate">{firstLine}</span>
            {secondLine && <span className="truncate">{secondLine}</span>}
          </p>
          <button
            type="button"
            onClick={() => void logout()}
            className="ml-6 cursor-pointer rounded text-xs leading-[22px] text-ink outline-accent hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 sm:ml-11"
          >
            Выйти
          </button>
        </div>
      </div>
    </header>
  );
}

export function Layout() {
  return (
    <div className="min-h-screen bg-page text-ink">
      <Header />
      <main className="mx-auto w-full max-w-[1440px] px-6 py-10 lg:px-16">
        <Outlet />
      </main>
    </div>
  );
}

export function NotFound() {
  const user = useSession((state) => state.user);

  return (
    <>
      <h1 className="text-[32px] leading-10 font-bold">Страница не найдена</h1>
      <p className="mt-2 text-sm leading-[22px] text-muted">Проверьте адрес или вернитесь на главную.</p>
      <Link
        to={user ? homeByRole[user.role] : '/'}
        className="mt-6 inline-flex h-11 items-center rounded-[10px] bg-accent px-4 text-sm leading-5 text-white outline-accent focus-visible:outline-2 focus-visible:outline-offset-2"
      >
        На главную
      </Link>
    </>
  );
}
