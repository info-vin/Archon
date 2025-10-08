# Simple Vite dev server setup
FROM node:18-alpine

WORKDIR /app

# Install system dependencies needed for some npm packages
RUN apk add --no-cache python3 make g++ git curl

# Install pnpm
RUN npm install -g pnpm

# Copy package files
COPY package.json pnpm-lock.yaml ./

# Install dependencies including dev dependencies for testing
RUN pnpm install --frozen-lockfile

# Create coverage directory with proper permissions
RUN mkdir -p /app/coverage && chmod 777 /app/coverage

# Copy source code
COPY . .

# Expose the port configured in package.json (3737)
EXPOSE 3737

# Start Vite dev server (already configured with --port 3737 --host in package.json)
CMD ["pnpm", "run", "dev"]