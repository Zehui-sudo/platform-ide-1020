FROM node:20-bookworm AS deps
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1 \
    CI=1 \
    NODE_OPTIONS=--max-old-space-size=2048
RUN corepack enable

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY .npmrc ./
COPY tsconfig.base.json ./
COPY web-learner/package.json web-learner/

# 仅安装前端所需依赖，供后续构建阶段复用
RUN pnpm install --frozen-lockfile --filter @platform-ide/web-learner...

FROM node:20-bookworm AS builder
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1 \
    CI=1 \
    NODE_OPTIONS=--max-old-space-size=2048
RUN corepack enable

COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/package.json ./package.json
COPY --from=deps /app/pnpm-lock.yaml ./pnpm-lock.yaml
COPY --from=deps /app/pnpm-workspace.yaml ./pnpm-workspace.yaml
COPY --from=deps /app/.npmrc ./.npmrc
COPY --from=deps /app/tsconfig.base.json ./tsconfig.base.json
COPY --from=deps /app/web-learner/package.json ./web-learner/package.json

COPY web-learner ./web-learner

ARG NEXT_PUBLIC_BACKEND_URL=""
ENV NEXT_PUBLIC_BACKEND_URL=${NEXT_PUBLIC_BACKEND_URL}

RUN pnpm --filter @platform-ide/web-learner build

FROM node:20-bookworm AS runner
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    NODE_OPTIONS=--max-old-space-size=2048
RUN corepack enable

COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/pnpm-workspace.yaml ./pnpm-workspace.yaml
COPY --from=builder /app/pnpm-lock.yaml ./pnpm-lock.yaml
COPY --from=builder /app/.npmrc ./.npmrc

COPY --from=builder /app/web-learner/.next ./web-learner/.next
COPY --from=builder /app/web-learner/public ./web-learner/public
COPY --from=builder /app/web-learner/package.json ./web-learner/package.json
COPY --from=builder /app/web-learner/next.config.ts ./web-learner/next.config.ts
COPY --from=builder /app/web-learner/scripts ./web-learner/scripts

EXPOSE 3000

CMD ["pnpm", "--filter", "@platform-ide/web-learner", "start"]
