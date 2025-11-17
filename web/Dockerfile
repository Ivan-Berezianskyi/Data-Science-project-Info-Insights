FROM node:20-alpine AS builder

WORKDIR /app

ARG API_BASE_URL=http://localhost:8000
ENV NODE_ENV=development \
    NITRO_PRESET=node-server \
    NUXT_TELEMETRY_DISABLED=1 \
    API_BASE_URL=${API_BASE_URL} \
    NUXT_PUBLIC_API_BASE_URL=${API_BASE_URL}

COPY package*.json ./
RUN npm install && npm rebuild esbuild

COPY . .
RUN npm run build


FROM node:20-alpine AS runner

WORKDIR /app

ARG API_BASE_URL=http://localhost:8000
ENV NODE_ENV=production \
    HOST=0.0.0.0 \
    PORT=3000 \
    NITRO_PORT=3000 \
    NITRO_HOST=0.0.0.0 \
    NITRO_PRESET=node-server \
    NUXT_TELEMETRY_DISABLED=1 \
    API_BASE_URL=${API_BASE_URL} \
    NUXT_PUBLIC_API_BASE_URL=${API_BASE_URL}

COPY --from=builder /app/.output ./.output

EXPOSE 3000

CMD ["node", ".output/server/index.mjs"]

