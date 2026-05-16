# ── Stage 1: Build the Vue app ──────────────────────────────────────────────
FROM node:22-slim AS builder

WORKDIR /app

# Install dependencies (layer cache)
COPY package.json package-lock.json* ./
RUN npm ci

# Copy source and build
COPY . .

# VITE_API_BASE_URL is set to /api so the frontend calls same-origin /api/*
# which Nginx proxies to the backend container — no CORS needed.
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build-only

# ── Stage 2: Serve with Nginx ────────────────────────────────────────────────
FROM nginx:1.27-alpine

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy our custom nginx config
COPY nginx.conf /etc/nginx/conf.d/app.conf

# Copy built Vue app from Stage 1
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
