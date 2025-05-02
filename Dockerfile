FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=wsgi.py

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies in specific order to avoid conflicts
COPY requirements.txt .
RUN pip install --no-cache-dir Werkzeug==2.0.1 && \
    pip install --no-cache-dir Flask==2.0.1 && \
    pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "wsgi:app"]