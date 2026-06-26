FROM node:20-alpine
WORKDIR /app
COPY package.json .
RUN npm install
COPY . .
# Собираем статику. Прод раздаём через `vite preview` — без dev-сервера,
# без HMR и вотчера файлов, поэтому страница не перезагружается сама.
RUN npm run build
EXPOSE 5173
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "5173"]
