# syntax=docker/dockerfile:1
# Build stage
FROM node:18-alpine AS builder
WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm ci

# Copy source and build
COPY . .
RUN npm run build

# Production stage
FROM nginx:stable-alpine

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port and start nginx
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
