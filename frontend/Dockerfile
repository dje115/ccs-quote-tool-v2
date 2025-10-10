# Development Dockerfile for React frontend
FROM node:20-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install all dependencies
RUN npm install

# Copy source code
COPY . .

# Expose port
EXPOSE 3000

# Set environment variable
ENV NODE_ENV=development

# Start development server
CMD ["npm", "start"]
