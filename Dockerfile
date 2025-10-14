FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy only your app files
COPY demo/ /app/
COPY src/ /app/src/
COPY prompts/ /app/prompts/
COPY models/ /app/models/

# Expose port
EXPOSE 8080

# Run FastAPI
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
