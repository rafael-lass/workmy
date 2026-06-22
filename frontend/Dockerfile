FROM node:20-alpine

WORKDIR /app

COPY package*.json ./

RUN npm install && npm audit fix || true

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]
