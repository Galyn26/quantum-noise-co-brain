# Use a lightweight, secure Python base image
FROM python:3.10-slim

WORKDIR /app

# Copy dependencies and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the server module and frontend templates
COPY server/ ./server/

EXPOSE 8000

# Run with Uvicorn bound to all interfaces for cloud mapping
CMD ["python", "server/app.py"]
