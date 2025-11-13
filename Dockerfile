# --------------------------
# Stage 1: Build frontend
# --------------------------
FROM public.ecr.aws/docker/library/node:18 AS frontend-builder

# Set working directory for frontend build
WORKDIR /app/demo/frontend

# Copy only frontend files
COPY demo/frontend/ .

# Install dependencies and build static site
RUN npm ci && npm run build

# --------------------------
# Stage 2: Final backend image
# --------------------------
FROM public.ecr.aws/docker/library/python:3.11-slim

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

# Copy static site output from frontend build into /app/static
COPY --from=frontend-builder /app/demo/frontend/out /app/static

# Expose FastAPI port
EXPOSE 8080

# Start the app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "4"]

