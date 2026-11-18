# Фронтенд бронирования аудиторий

React, TypeScript и Vite. Стили собирает Tailwind CSS. Модули страниц в
`src/modules/user.tsx` и `src/modules/admin.tsx` отвечают за маршруты `/` и
`/admin` соответственно. Axios-клиент находится в `src/api.ts`. Zustand хранит
состояние запроса в `src/api-status.ts`. В административном разделе пока доступна
только проверка соединения с публичным `GET /api/v1/health`. Доступ к будущим
административным операциям должен проверяться в FastAPI.

## Локальный запуск

Установите Node.js **24.13.1** с npm **11.8.0**. При использовании nvm
выполните `nvm install 24.13.1` и `nvm use 24.13.1`. Проверьте версии командами
`node --version` и `npm --version`. Запустите FastAPI по
[инструкции проекта](../README.md). Затем из каталога `frontend` выполните:

```sh
npm ci
npm run dev
```

Откройте <http://localhost:5000>. На странице `/admin` нажмите
«Проверить подключение». Vite передаёт запросы к `/api` и `/public`
на FastAPI по адресу `http://127.0.0.1:4001`. Для браузера запросы остаются
на том же origin, поэтому изменять CORS для этой схемы не нужно.

При необходимости скопируйте `.env.example` в `.env.local` и измените
`API_PROXY_TARGET` для локального прокси. `VITE_API_BASE_URL` по умолчанию
равен `/api/v1`. Если задать полный URL API другого origin, запросы идут
напрямую и этот origin фронтенда нужно разрешить в `networking.frontend.origin`
на стороне FastAPI. Значения `VITE_*` видны в браузере. Храните секреты на сервере.
После изменения переменных перезапустите Vite или пересоберите фронтенд.

## Проверки и production

Из каталога `frontend`:

```sh
npm ci
npm run lint
npm run typecheck
npm run build
```

Эти команды использует проверка `Frontend` из DEV-01. Сборка создаёт каталог
`dist/`. Для её обслуживания установите [Caddy 2](https://caddyserver.com/docs/install)
и из того же каталога выполните:

```sh
caddy validate --config Caddyfile
caddy run --config Caddyfile
```

Откройте напрямую <http://127.0.0.1:8080/admin>. Caddy отдаёт SPA для вложенных
маршрутов и передаёт `/api` и `/public` в FastAPI, сохраняя путь. Для размещения
задайте процессу Caddy `SITE_ADDRESS` (публичный домен для HTTPS), `SITE_BIND`
(интерфейс, принимающий внешние подключения, например `0.0.0.0`) и
`API_UPSTREAM` (адрес FastAPI, например `127.0.0.1:4001`). `dist/` и `Caddyfile` разверните
в рабочем каталоге Caddy. Проверка `/health` подтверждает доступность HTTP API.
