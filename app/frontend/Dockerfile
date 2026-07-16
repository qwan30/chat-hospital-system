FROM oven/bun:alpine AS builder
WORKDIR /app

# Copy package management files
COPY package.json bun.lockb ./
RUN bun install --frozen-lockfile

# Copy source code and build
COPY . .
RUN bun run build

FROM oven/bun:alpine AS runner
WORKDIR /app

# Non-root user for security
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

# Copy built application from builder
COPY --from=builder --chown=appuser:appgroup /app/.output ./.output

EXPOSE 8082
ENV PORT=8082
ENV NODE_ENV=production

# Start the nitro server
CMD ["bun", "run", ".output/server/index.mjs"]
