# Use an official Python runtime
FROM python:3.11-slim

# Set environment variables to prevent Python from writing .pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Expose a default port 
EXPOSE 8081

# Command to run the API
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8081}"]