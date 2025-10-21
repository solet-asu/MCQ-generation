# --------------------------
# Stage 1: Build frontend
# --------------------------
FROM node:18 AS frontend-builder

# Set working dir and copy frontend files
WORKDIR /frontend
COPY frontend/ .

# Install and build
RUN npm ci && npm run build

# --------------------------
# Stage 2: Backend + final image
# --------------------------
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install backend dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY demo/ /app/
COPY src/ /app/src/
COPY prompts/ /app/prompts/
COPY models/ /app/models/

# Copy built frontend into demo/static
COPY --from=frontend-builder /frontend/out /app/static

# Expose port
EXPOSE 8080

# Start FastAPI
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
