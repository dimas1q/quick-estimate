## frontend/Dockerfile
FROM node:20

WORKDIR /app

# Сначала копируем только package.json и package-lock.json, чтобы кэшировать install
COPY package*.json ./

RUN npm install

# Потом копируем всё остальное
COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev"]
