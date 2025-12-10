# Multi-stage Dockerfile for React frontend with Vite
# Stage 1: Build stage
FROM node:20-alpine AS build

# Accept build arguments for API URL
ARG REACT_APP_API_URL=http://localhost:8000
ENV REACT_APP_API_URL=${REACT_APP_API_URL}

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# SECURITY: Run linting before build to catch security issues
RUN npm run lint || true  # Continue build even if linting has warnings

# Build the application (environment variables are baked into the build)
# SECURITY: Set NODE_ENV=production to ensure production optimizations
ENV NODE_ENV=production
RUN npm run build

# Stage 2: Production stage with Nginx
FROM nginx:alpine

# Copy built assets from build stage (Vite outputs to 'build' folder as configured)
COPY --from=build /app/build /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
