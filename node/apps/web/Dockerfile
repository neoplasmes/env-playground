# syntax=docker/dockerfile:1.7
FROM node:26.10.0-slim AS base
RUN npm install -g pnpm@12.6.0
WORKDIR /workspace/node
FROM base AS dependencies
COPY node/package.json node/pnpm-workspace.yaml node/pnpm-lock.yaml ./
COPY node/apps/web/package.json apps/web/package.json
RUN --mount=type=cache,target=/root/.local/share/pnpm/store pnpm install --frozen-lockfile
FROM dependencies AS build
COPY node/apps/web apps/web
ENV NEXT_TELEMETRY_DISABLED=1
RUN pnpm --filter @playground/web build
FROM node:26.10.0-slim AS runtime
WORKDIR /app
RUN groupadd -g 10001 app && useradd -u 10001 -g app app
COPY --from=build --chown=app:app /workspace/node/apps/web/.next/standalone ./
COPY --from=build --chown=app:app /workspace/node/apps/web/.next/static ./apps/web/.next/static
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 HOSTNAME=0.0.0.0 PORT=3000
USER 10001:10001
EXPOSE 3000
CMD ["node","apps/web/server.js"]
