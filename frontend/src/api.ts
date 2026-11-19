import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios';

const ACCESS_KEY = 'booking-manager.token';
const REFRESH_KEY = 'booking-manager.refresh-token';

export interface ApiError {
  message: string;
  status_code: number;
  code: string;
  errors?: { field: string; message: string }[];
}

export const tokens = {
  access: () => localStorage.getItem(ACCESS_KEY),
  refresh: () => localStorage.getItem(REFRESH_KEY),
  save(access: string, refresh?: string) {
    localStorage.setItem(ACCESS_KEY, access);
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
  },
  clear() {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL?.trim() || '/api/v1',
  timeout: 5000,
  headers: { Accept: 'application/json' },
});

type RetryConfig = InternalAxiosRequestConfig & { retried?: boolean };

const isAuthRequest = (config: InternalAxiosRequestConfig) => config.url?.startsWith('/auth/') ?? false;

let expiredHandler = () => {};

export function onSessionExpired(handler: () => void) {
  expiredHandler = handler;
}

let refreshing: Promise<string> | null = null;

function refreshToken() {
  refreshing ??= api
    .post<{ token: string }>('/auth/refresh', { refresh_token: tokens.refresh() })
    .then(({ data }) => {
      tokens.save(data.token);
      return data.token;
    })
    .finally(() => {
      refreshing = null;
    });
  return refreshing;
}

api.interceptors.request.use((config) => {
  const token = tokens.access();
  if (token && !isAuthRequest(config)) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(undefined, async (error: AxiosError) => {
  const config = error.config as RetryConfig | undefined;
  if (error.response?.status !== 401 || !config || isAuthRequest(config)) throw error;

  if (!config.retried && tokens.refresh()) {
    config.retried = true;
    const token = await refreshToken().catch(() => null);
    if (token) return api(config);
  }

  tokens.clear();
  expiredHandler();
  throw error;
});
