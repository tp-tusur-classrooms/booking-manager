import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import { defineConfig, loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
  const { API_PROXY_TARGET } = loadEnv(mode, process.cwd(), 'API_PROXY_');
  const target = API_PROXY_TARGET || 'http://127.0.0.1:4001';

  return {
    plugins: [react(), tailwindcss()],
    server: {
      port: 5000,
      strictPort: true,
      proxy: {
        '^/api(?:/|$)': { target },
        '^/public(?:/|$)': { target },
      },
    },
  };
});
