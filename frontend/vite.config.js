// vite.config.js
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Прод раздаётся как собранная статика через `vite preview` (см. Dockerfile):
// нет dev-сервера, нет HMR/websocket и вотчера файлов → страница сама не
// перезагружается. Блок server ниже нужен только для локального `npm run dev`.

const proxyApi = {
  "/api": {
    // Внутри docker-сети backend доступен по имени контейнера на порту 8000
    // (8002 — это публикация на хост, внутри сети её нет).
    target: "http://ku_grant_api:8000",
    changeOrigin: true,
  },
};

const allowedHosts = ["ku-grant.aican.cloud", "localhost", "127.0.0.1"];

export default defineConfig({
  plugins: [react()],

  // Раздача собранной статики (npm run preview) — то, что крутится в контейнере.
  preview: {
    host: true,
    port: 5173,
    allowedHosts,
    proxy: proxyApi,
  },

  // Локальная разработка (npm run dev). В контейнере НЕ используется.
  server: {
    host: true,
    port: 5173,
    allowedHosts,
    hmr: process.env.VITE_HMR === "on", // по умолчанию выключен
    proxy: proxyApi,
  },
});
