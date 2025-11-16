FROM node:18-alpine AS base

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

FROM base AS development

RUN npm install --save-dev webpack webpack-cli

COPY . .

EXPOSE 3001

CMD ["npm", "start"]

FROM base AS production

COPY . .
RUN npm run build

EXPOSE 3001

CMD ["npm", "run", "serve"]
