import '@fontsource-variable/inter/index.css';
import { StrictMode, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, Route, Routes } from 'react-router';
import { Layout, NotFound, RequireAuth, RequireRole } from './layout';
import { AdminPage } from './modules/admin';
import { LoginPage } from './modules/login';
import { UserPage } from './modules/user';
import { useSession } from './session';
import './styles.css';

function App() {
  const restore = useSession((state) => state.restore);

  useEffect(() => {
    void restore();
  }, [restore]);

  return (
    <Routes>
      <Route path="login" element={<LoginPage />} />
      <Route element={<RequireAuth />}>
        <Route element={<Layout />}>
          <Route element={<RequireRole role="user" />}>
            <Route index element={<UserPage />} />
          </Route>
          <Route element={<RequireRole role="admin" />}>
            <Route path="admin" element={<AdminPage />} />
          </Route>
          <Route path="*" element={<NotFound />} />
        </Route>
      </Route>
    </Routes>
  );
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
);
