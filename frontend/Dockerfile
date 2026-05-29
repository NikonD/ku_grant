FROM node:20-alpine
WORKDIR /app
COPY package.json .
RUN npm install
COPY . .
RUN chmod -R 777 /app/node_modules
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]