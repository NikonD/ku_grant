// vite.config.js
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// За обратным прокси (nginx + HTTPS) websocket HMR рвётся и Vite циклически
// перезагружает страницу. Поэтому HMR ВЫКЛЮЧЕН по умолчанию.
// Нужен хот-релоад локально — запускай с VITE_HMR=on.
const HMR_ENABLED = process.env.VITE_HMR === "on" || process.env.VITE_HMR === "true";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    // Разрешаем доступ по доменному имени (за реверс-прокси).
    allowedHosts: ["ku-grant.aican.cloud", "localhost", "127.0.0.1"],
    // false → клиент Vite не открывает websocket и не делает авто-reload.
    hmr: HMR_ENABLED
      ? { host: "ku-grant.aican.cloud", protocol: "wss", clientPort: 443 }
      : false,
    proxy: {
      "/api": {
        target: "http://backend:8000",
        changeOrigin: true,
      },
    },
  },
});
