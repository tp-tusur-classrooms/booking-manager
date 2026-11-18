import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, Link, NavLink, Route, Routes } from 'react-router';
import { AdminPage } from './modules/admin';
import { UserPage } from './modules/user';
import './styles.css';

function App() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-950">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-4xl flex-wrap items-center justify-between gap-x-8 gap-y-3 px-5 py-4">
          <Link to="/" className="font-semibold">
            Бронирование аудиторий ТУСУР
          </Link>
          <nav aria-label="Разделы" className="flex flex-wrap gap-4 text-sm">
            <NavLink end to="/" className="aria-[current=page]:font-semibold">
              Аудитории
            </NavLink>
            <NavLink to="/admin" className="aria-[current=page]:font-semibold">
              Администрирование
            </NavLink>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-4xl px-5 py-12">
        <Routes>
          <Route index element={<UserPage />} />
          <Route path="admin" element={<AdminPage />} />
          <Route
            path="*"
            element={
              <>
                <h1 className="text-2xl font-semibold">Страница не найдена</h1>
                <Link to="/" className="mt-4 inline-block text-blue-800 underline">
                  К списку аудиторий
                </Link>
              </>
            }
          />
        </Routes>
      </main>
    </div>
  );
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
);
