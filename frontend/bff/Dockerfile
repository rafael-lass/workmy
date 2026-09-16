# ─── Dockerfile do BFF Node.js ───────────────────────────────────────────────
FROM node:20-alpine AS runtime

# Cria usuário não-root
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
WORKDIR /app

# Copia package.json e instala dependências (aproveitando cache de camadas)
COPY package.json package-lock.json* ./
RUN npm ci --omit=dev --ignore-scripts

# Copia o código do servidor
COPY server.js .

ENV NODE_ENV=production \
    PORT=3000

USER appuser
EXPOSE 3000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000/health', r => process.exit(r.statusCode === 200 ? 0 : 1))" || exit 1

CMD ["node", "server.js"]
