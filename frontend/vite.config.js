// vite.config.js
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// HMR (hot reload) за обратным прокси (traefik / HTTPS-домен) часто не может
// поднять websocket: клиент Vite стучится не на тот хост/порт, соединение
// рвётся, и при каждом реконнекте делается полная перезагрузка страницы —
// то самое «фронт ребутится на ровном месте». Управляем через env:
//   VITE_HMR=off                    — полностью выключить HMR (для деплоя)
//   VITE_HMR_HOST=grant.example.kz  — публичный домен (HMR через wss:443)
// По умолчанию (локальная разработка) — обычный HMR, ничего не меняется.
function hmrConfig() {
  if (process.env.VITE_HMR === "off" || process.env.VITE_HMR === "false") {
    return false;
  }
  if (process.env.VITE_HMR_HOST) {
    return { host: process.env.VITE_HMR_HOST, clientPort: 443, protocol: "wss" };
  }
  return true; // дефолт — локальный HMR
}

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    hmr: hmrConfig(),
    // Проксируем API запросы на бэкенд (чтобы не было CORS в dev режиме)
    proxy: {
      "/api": {
        target: "http://backend:8000",
        changeOrigin: true,
      },
    },
  },
});
