# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Prevent .pyc and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# --- Optional: build deps (needed if you compile wheels like psycopg2) ---
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential gcc libpq-dev \
#   && rm -rf /var/lib/apt/lists/*

# Create app dir and non-root user
WORKDIR /app
RUN useradd -u 10001 -m appuser

# Install Python deps first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project
COPY . .

# If you use a start script, ensure it’s executable
# (prefer a literal mode; no need for ARG indirection)
COPY --chmod=0755 start.sh /app/start.sh

# Expose app port (NOT Postgres)
EXPOSE 8000

# Run as non-root
USER appuser

# EITHER: run via start.sh (uncomment next line and remove CMD below)
# CMD ["/app/start.sh"]

# OR: run Uvicorn directly
CMD ["uvicorn", "django_main.asgi:application", "--host", "0.0.0.0", "--port", "8000"]
