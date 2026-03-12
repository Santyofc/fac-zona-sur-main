FROM node:20-alpine AS builder
WORKDIR /app
RUN npm install -g pnpm
COPY package.json pnpm-lock.yaml* ./
RUN pnpm install --frozen-lockfile
COPY . .
RUN pnpm build

FROM node:20-alpine AS runner
WORKDIR /app
RUN npm install -g pnpm
COPY --from=builder /app/.output ./.output
EXPOSE 3000
ENV HOST=0.0.0.0 PORT=3000 NODE_ENV=production
CMD ["node", ".output/server/index.mjs"]
