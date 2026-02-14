FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# Copy source
COPY frontend .

# Build
ENV NEXT_PUBLIC_API_URL=http://localhost:8000
RUN npm run build

# Expose port
EXPOSE 3000

# Run
CMD ["npm", "start"]
