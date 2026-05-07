# Stage 1: Build
FROM node:20-slim AS builder
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
ARG VITE_API_URL=http://localhost:8000
ARG VITE_AZURE_CLIENT_ID=placeholder
ARG VITE_AZURE_TENANT_ID=placeholder
ARG VITE_AZURE_BACKEND_SCOPE=placeholder
ENV VITE_API_URL=$VITE_API_URL \
    VITE_AZURE_CLIENT_ID=$VITE_AZURE_CLIENT_ID \
    VITE_AZURE_TENANT_ID=$VITE_AZURE_TENANT_ID \
    VITE_AZURE_BACKEND_SCOPE=$VITE_AZURE_BACKEND_SCOPE
RUN npm run build

# Stage 2: Serve
FROM nginx:alpine AS runtime
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
