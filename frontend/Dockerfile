# Frontend Dockerfile for Next.js (Development)
# Firebase JS SDK >=12 requires Node 20+, so use a 20.x base image.
FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install all dependencies (including dev for development)
RUN npm ci

# Copy source code
COPY . .

# Expose port
EXPOSE 3000

# Start in development mode
CMD ["npm", "run", "dev"]
