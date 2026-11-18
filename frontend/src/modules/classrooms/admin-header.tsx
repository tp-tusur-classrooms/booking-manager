import { NavLink, Link, useNavigate } from 'react-router';
import logo from '../../assets/classrooms-logo.svg';
import bell from '../../assets/notifications.svg';
import type { AdminProfile } from './api';

export function AdminHeader({ profile }: { profile?: AdminProfile }) {
  const navigate = useNavigate();
  const name = profile?.name?.trim();
  const parts = name?.split(/\s+/) ?? [];
  const initials = parts.slice(0, 2).map((part) => Array.from(part)[0]).join('').toUpperCase();
  const unread = profile?.unread_notifications ?? 0;

  function signOut() {
    sessionStorage.removeItem('access_token');
    sessionStorage.removeItem('refresh_token');
    void navigate('/', { replace: true });
  }

  return (
    <header className="border-b border-[#e4e4ea] bg-white text-[#242529]">
      <div className="mx-auto flex min-h-[87px] max-w-[1440px] flex-wrap items-stretch gap-x-5 px-5 lg:grid lg:grid-cols-[minmax(0,334px)_1fr_auto] lg:px-16">
        <Link to="/" className="flex items-center gap-[10px] text-xl font-bold text-black">
          <img src={logo} alt="" className="shrink-0" />
          Аудитории
        </Link>
        <nav aria-label="Разделы администратора" className="flex">
          <NavLink to="/admin" className="relative flex min-h-12 items-center text-sm aria-[current=page]:font-bold after:absolute after:inset-x-0 after:bottom-0 after:h-[3px] after:bg-[#6952b3]">
            Управление
          </NavLink>
        </nav>
        {profile && (
          <div className="ml-auto flex min-h-12 items-center gap-4 sm:gap-6">
            <span className="relative flex size-7 items-center justify-center" role="img"
              aria-label={unread > 0 ? `Непрочитанных уведомлений: ${unread}` : 'Уведомления'}>
              <img src={bell} alt="" />
              {unread > 0 && (
                <span className="absolute -top-2 -right-1 grid min-h-[18px] min-w-[18px] place-items-center rounded-full bg-[#6952b3] px-1 text-[10px] text-white">
                  {unread > 99 ? '99+' : unread}
                </span>
              )}
            </span>
            <div className="flex items-center gap-3 border-l border-[#e4e4ea] pl-4 sm:pl-6">
              <span aria-hidden="true" className="grid size-10 shrink-0 place-items-center rounded-full bg-[#ebe7df] text-[13px] font-bold text-black">
                {initials || 'А'}
              </span>
              <span className="max-w-32 text-[13px] leading-5 text-black">
                {parts.length > 0 ? <>{parts[0]}{parts.length > 1 && <><br />{parts.slice(1).join(' ')}</>}</> : 'Администратор'}
              </span>
            </div>
            <button type="button" onClick={signOut} className="cursor-pointer text-xs hover:underline">
              Выйти
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
