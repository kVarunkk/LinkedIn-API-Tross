FROM python:3.11-slim

# Prevent Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Run uvicorn on port 8080 (Cloud Run's default expected port)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]