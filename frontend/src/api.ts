import axios from 'axios';

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL?.trim() || '/api/v1',
  timeout: 5000,
  headers: { Accept: 'application/json' },
});
