FROM node:20-alpine

WORKDIR /app

COPY . /app

RUN npm install

WORKDIR /app/apps/web

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--hostname", "0.0.0.0", "--port", "3000"]
