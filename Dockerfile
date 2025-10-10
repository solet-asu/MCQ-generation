# Use lightweight base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install Poetry
RUN pip install --upgrade pip && pip install poetry

# Copy the dependency files first (for caching)
COPY pyproject.toml poetry.lock* /app/

# Configure Poetry
RUN poetry config virtualenvs.create false \
 && poetry install --no-root --no-interaction --no-ansi

# Copy rest of your app
COPY demo/ /app/

# Expose port for App Runner
EXPOSE 8080

# Run FastAPI app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
